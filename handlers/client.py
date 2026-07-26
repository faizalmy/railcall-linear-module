"""Linear GraphQL client with retry logic and rate limiting."""

import os
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
        """Create requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": self.api_key,
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
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        last_error: Optional[Exception] = None
        
        for attempt in range(self.MAX_RETRIES + 1):
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
                    retry_after = int(response.headers.get("Retry-After", 10))
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds.",
                        code="RATE_LIMITED",
                    )
                
                response.raise_for_status()
                
                # Parse GraphQL response
                result = response.json()
                
                # Check for GraphQL errors
                handle_graphql_errors(result)
                
                return result.get("data", {})
                
            except requests.exceptions.Timeout as e:
                last_error = NetworkError(f"Request timeout after {timeout}s: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                last_error = NetworkError(f"Connection error: {str(e)}")
            except requests.exceptions.RequestException as e:
                last_error = NetworkError(f"Request failed: {str(e)}")
            except LinearError as e:
                # Don't retry authentication errors
                if isinstance(e, AuthenticationError):
                    raise
                last_error = e
            
            # Wait before retry (exponential backoff)
            if attempt < self.MAX_RETRIES:
                wait_time = (self.RETRY_BACKOFF ** attempt) + (0.1 * attempt)
                time.sleep(wait_time)
        
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
