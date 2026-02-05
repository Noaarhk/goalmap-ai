from typing import Any, Dict


class AppException(Exception):
    """Base exception for all application-specific errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Any = None,
        headers: Dict[str, str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.headers = headers


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", detail: Any = None):
        super().__init__(message, status_code=404, detail=detail)


class ValidationException(AppException):
    """Input validation failed."""

    def __init__(self, message: str = "Validation failed", detail: Any = None):
        super().__init__(message, status_code=400, detail=detail)


class ResourceConflictException(AppException):
    """Resource already exists or state conflict."""

    def __init__(self, message: str = "Resource conflict", detail: Any = None):
        super().__init__(message, status_code=409, detail=detail)


class AuthenticationException(AppException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed", detail: Any = None):
        super().__init__(
            message,
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
