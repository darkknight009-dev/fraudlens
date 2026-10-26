"""Typed SDK failures."""


class FraudLensError(Exception):
    """Base class for all client errors."""

    def __init__(
        self, message: str, *, code: str | None = None, request_id: str | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.request_id = request_id


class AuthenticationError(FraudLensError):
    pass


class ValidationError(FraudLensError):
    pass


class RateLimitError(FraudLensError):
    pass


class TimeoutError(FraudLensError):
    pass


class ServerError(FraudLensError):
    pass
