class BahnAPIError(Exception):
    """Base exception for BahnAPI issues."""


class AuthenticationError(BahnAPIError):
    """Raised when authentication against the DB API fails."""


class RateLimitError(BahnAPIError):
    """Raised when the API reports rate limiting."""


class StationLookupError(BahnAPIError):
    """Raised when station lookup is ambiguous or fails."""
