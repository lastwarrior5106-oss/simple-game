from .generic import (
    HTTPError,
    ServiceError,
    ValidationError,
    AuthorizationError,
    ForbiddenError,
    BadRequestError,
    NotFoundError,
    MethodNotAllowedError,
    TooManyRequestsError,
)

UserNotFoundError = NotFoundError
TeamNotFoundError = NotFoundError

TeamNameTakenError = BadRequestError
TeamFullError = BadRequestError
AlreadyInTeamError = BadRequestError
NotInTeamError = BadRequestError
InsufficientCoinsError = BadRequestError

__all__ = [
    "HTTPError",
    "ServiceError",
    "ValidationError",
    "AuthorizationError",
    "ForbiddenError",
    "BadRequestError",
    "NotFoundError",
    "MethodNotAllowedError",
    "TooManyRequestsError",
    "UserNotFoundError",
    "TeamNotFoundError",
    "TeamNameTakenError",
    "TeamFullError",
    "AlreadyInTeamError",
    "NotInTeamError",
    "InsufficientCoinsError",
]