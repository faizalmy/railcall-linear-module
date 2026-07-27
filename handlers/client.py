"""Linear GraphQL client with retry logic and rate limiting.

Transport is stdlib urllib only. The module is exec'd as a single file inside
the RailCall Studio where third-party packages are not guaranteed, and a
module making a handful of HTTP calls does not justify the supply-chain
surface of a dependency. The Studio's own http_post_json helper is unusable
here because it collapses errors into a bare RuntimeError, discarding the
status code and Retry-After header that the retry loop needs.
"""

import json as _json
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .credentials import in_studio, resolve_api_key
from .utils.errors import (
    LinearError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    handle_graphql_errors,
)


class _Response:
    """The slice of a HTTP response the retry loop actually reads."""

    def __init__(self, status_code: int, headers: Dict[str, str], body: bytes):
        self.status_code = status_code
        self.headers = headers
        self._body = body

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")

    def json(self) -> Dict[str, Any]:
        parsed: Dict[str, Any] = _json.loads(self._body.decode("utf-8"))
        return parsed


class LinearClient:
    """Linear GraphQL API client with automatic retry and rate limiting."""

    LINEAR_API_URL = "https://api.linear.app/graphql"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_BACKOFF = 2
    MAX_BACKOFF = 60

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Linear client.
        
        Args:
            api_key: Linear API key. If not provided, reads from LINEAR_API_KEY env var.
        """
        self.api_key = api_key or resolve_api_key()
        if not self.api_key:
            # Point at the source that actually applies here; naming the other
            # one would send the operator to a place this context ignores.
            if in_studio():
                raise AuthenticationError(
                    "No Linear credential in the station vault. Save your API key "
                    "under the 'linear' provider (Studio → Sends → Configure). "
                    "Get the key from Linear → Settings → API → Create key."
                )
            raise AuthenticationError(
                "No Linear API key. Set LINEAR_API_KEY in the environment. "
                "Get your key from Linear → Settings → API → Create key."
            )

    def _backoff_seconds(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Seconds to wait before the next attempt.

        Honors a server-supplied Retry-After when present; otherwise uses capped
        exponential backoff with full jitter to avoid synchronized retries.
        """
        if retry_after is not None:
            return min(retry_after, self.MAX_BACKOFF)

        window = min(self.RETRY_BACKOFF ** attempt, self.MAX_BACKOFF)
        return random.uniform(0, window)

    @staticmethod
    def _parse_retry_after(response: "_Response") -> Optional[float]:
        """Read the Retry-After header as seconds, if it is present and numeric."""
        raw = response.headers.get("Retry-After")
        if raw is None:
            return None
        try:
            return max(0.0, float(raw))
        except ValueError:
            # Retry-After may also be an HTTP-date; fall back to normal backoff.
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": self.api_key or "",
            "Content-Type": "application/json",
        }
    
    @staticmethod
    def is_mutation(query: str) -> bool:
        """Whether this document mutates state.

        Linear's GraphQL API offers no idempotency key, so a retry after a
        mutation the server already accepted creates a duplicate issue or
        comment. Detecting it here rather than at the call sites means a new
        command cannot forget to opt out of retries.
        """
        return query.lstrip().startswith("mutation")

    def _post(self, payload: Dict[str, Any], timeout: int) -> "_Response":
        """One HTTP round trip. Raises NetworkError on any transport failure."""
        request = urllib.request.Request(
            self.LINEAR_API_URL,
            data=_json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=self._get_headers(),
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as raw:
                return _Response(raw.getcode(), dict(raw.headers), raw.read())
        except urllib.error.HTTPError as e:
            # A 4xx/5xx is a real response - the loop decides whether to retry,
            # so it must survive with its status and headers intact.
            body = b""
            try:
                body = e.read()
            except Exception:
                pass
            return _Response(e.code, dict(e.headers or {}), body)
        except urllib.error.URLError as e:
            raise NetworkError(f"Network error: {e.reason}")
        except TimeoutError as e:
            raise NetworkError(f"Request timeout after {timeout}s: {str(e)}")

    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """Execute GraphQL query with retry and error handling.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            timeout: Request timeout in seconds
            
        Returns:
            GraphQL response data

        Raises:
            LinearError: If query fails after retries
        """
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        # Mutations get exactly one attempt. Linear has no idempotency key, so a
        # 429 or timeout arriving AFTER the server accepted the write would be
        # retried into a duplicate issue/comment. Recovery is a fresh airlock
        # approval, which is a human decision rather than a silent replay.
        attempts = 1 if self.is_mutation(query) else self.MAX_RETRIES + 1
        last_attempt = attempts - 1

        last_error: Optional[Exception] = None

        for attempt in range(attempts):
            retry_after: Optional[float] = None

            try:
                response = self._post(payload, timeout)

                # Handle HTTP errors
                if response.status_code == 401:
                    # Name the credential store that actually applies here.
                    # Pointing a Studio operator at an env var they never set
                    # would send them somewhere this context does not read.
                    if in_studio():
                        raise AuthenticationError(
                            "Invalid Linear API key in the station vault under the "
                            "'linear' provider. Replace it in Studio → Sends → Configure."
                        )
                    raise AuthenticationError(
                        "Invalid Linear API key. Check LINEAR_API_KEY in the environment."
                    )

                if response.status_code == 429:
                    retry_after = self._parse_retry_after(response)
                    raise RateLimitError(
                        "Rate limit exceeded."
                        + (f" Server asked to retry after {retry_after:.0f}s." if retry_after else ""),
                        code="RATE_LIMITED",
                        details={"retry_after": retry_after},
                    )

                # 4xx other than 429 are caller mistakes - retrying cannot help
                if 400 <= response.status_code < 500:
                    raise LinearError(
                        f"Linear API returned HTTP {response.status_code}: {response.text[:200]}",
                        code=f"HTTP_{response.status_code}",
                    )

                if response.status_code >= 500:
                    raise NetworkError(
                        f"Linear API returned HTTP {response.status_code} - retrying."
                    )

                # Parse GraphQL response
                result = response.json()

                # Check for GraphQL errors
                handle_graphql_errors(result)

                data: Dict[str, Any] = result.get("data", {})
                return data

            except LinearError as e:
                # Only transient failures are worth another attempt. Auth, validation,
                # not-found and permission errors are deterministic.
                if not isinstance(e, (RateLimitError, NetworkError)):
                    raise
                # A mutation never retries, so surface the error with its
                # Retry-After intact for the caller to act on.
                if attempts == 1:
                    raise
                last_error = e

            # Wait before retry (capped exponential backoff with jitter)
            if attempt < last_attempt:
                time.sleep(self._backoff_seconds(attempt, retry_after))

        # All retries exhausted
        if last_error:
            raise last_error
        raise LinearError("Query failed after all retries")
    
    def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute GraphQL query (alias for execute)."""
        return self.execute(query, variables, **kwargs)
    
    def mutate(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute GraphQL mutation (alias for execute)."""
        return self.execute(mutation, variables, **kwargs)


# Global client instance (initialized lazily)
_client: Optional[LinearClient] = None


def get_client() -> LinearClient:
    """Get or create global Linear client instance."""
    global _client
    if _client is None:
        _client = LinearClient()
    return _client


def execute_query(
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Execute GraphQL query using global client.
    
    Args:
        query: GraphQL query string
        variables: Optional query variables
        
    Returns:
        GraphQL response data
    """
    return get_client().execute(query, variables, **kwargs)
