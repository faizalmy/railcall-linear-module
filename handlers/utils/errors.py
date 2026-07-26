"""Error handling utilities for Linear API interactions."""

from typing import Optional, Dict, Any


class LinearError(Exception):
    """Base exception for Linear API errors."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(LinearError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(LinearError):
    """Raised when user lacks permissions."""
    pass


class ValidationError(LinearError):
    """Raised when input validation fails."""
    pass


class RateLimitError(LinearError):
    """Raised when rate limit is hit."""
    pass


class NotFoundError(LinearError):
    """Raised when resource doesn't exist."""
    pass


class NetworkError(LinearError):
    """Raised when network request fails."""
    pass


def handle_graphql_errors(response: Dict[str, Any]) -> None:
    """Parse GraphQL errors and raise appropriate exceptions.
    
    Args:
        response: GraphQL response dict
        
    Raises:
        LinearError: Appropriate subclass based on error code
    """
    if "errors" not in response:
        return
    
    error = response["errors"][0]
    message = error.get("message", "Unknown error")
    extensions = error.get("extensions", {})
    code = extensions.get("code")
    
    # Map Linear error codes to exceptions
    if code == "AUTHENTICATION_ERROR":
        raise AuthenticationError(
            "Invalid API key or expired OAuth token. Run `railcall connect linear` to re-authenticate.",
            code=code,
            details=extensions
        )
    elif code == "AUTHORIZATION_ERROR":
        raise AuthorizationError(
            "Insufficient permissions. Contact your Linear admin to request access.",
            code=code,
            details=extensions
        )
    elif code == "VALIDATION_ERROR":
        raise ValidationError(
            f"Invalid input: {message}",
            code=code,
            details=extensions
        )
    elif code == "NOT_FOUND":
        raise NotFoundError(
            f"Resource not found: {message}",
            code=code,
            details=extensions
        )
    elif code == "RATE_LIMITED":
        raise RateLimitError(
            "Rate limit exceeded. Retrying automatically...",
            code=code,
            details=extensions
        )
    else:
        raise LinearError(
            f"Linear API error: {message}",
            code=code,
            details=extensions
        )
