"""Linear GraphQL client with retry logic and rate limiting."""

import os
import random
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter

from .utils.errors import (
    LinearError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    handle_graphql_errors,
)


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
        self.api_key = api_key or os.environ.get("LINEAR_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "LINEAR_API_KEY environment variable not set. "
                "Get your key from Linear → Settings → API → Create key."
            )
        
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session for connection pooling.

        Retries are handled entirely in execute() so that Retry-After is honored
        and every attempt is counted once. Stacking urllib3's Retry on top of the
        loop would multiply the two limits together (4 x 4 = 16 requests per call).
        """
        session = requests.Session()

        adapter = HTTPAdapter(max_retries=0, pool_connections=4, pool_maxsize=8)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

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
    def _parse_retry_after(response: requests.Response) -> Optional[float]:
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
        
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES + 1):
            retry_after: Optional[float] = None

            try:
                response = self.session.post(
                    self.LINEAR_API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=timeout,
                )

                # Handle HTTP errors
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid API key. Check your LINEAR_API_KEY environment variable."
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

                response.raise_for_status()

                # Parse GraphQL response
                result = response.json()

                # Check for GraphQL errors
                handle_graphql_errors(result)

                data: Dict[str, Any] = result.get("data", {})
                return data

            except requests.exceptions.Timeout as e:
                last_error = NetworkError(f"Request timeout after {timeout}s: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                last_error = NetworkError(f"Connection error: {str(e)}")
            except requests.exceptions.RequestException as e:
                last_error = NetworkError(f"Request failed: {str(e)}")
            except LinearError as e:
                # Only transient failures are worth another attempt. Auth, validation,
                # not-found and permission errors are deterministic.
                if not isinstance(e, (RateLimitError, NetworkError)):
                    raise
                last_error = e

            # Wait before retry (capped exponential backoff with jitter)
            if attempt < self.MAX_RETRIES:
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
