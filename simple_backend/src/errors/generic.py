from fastapi import HTTPException
from http import HTTPStatus


class HTTPError(HTTPException):
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    detail: str = "Internal Server Error"

    def __init__(self, detail: str = None):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
        )


class ServiceError(HTTPError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    detail = "Service Error"


class ValidationError(HTTPError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    detail = "Validation Error"


class AuthorizationError(HTTPError):
    status_code = HTTPStatus.UNAUTHORIZED
    detail = "Authorization Error"


class ForbiddenError(HTTPError):
    status_code = HTTPStatus.FORBIDDEN
    detail = "Forbidden Error"


class BadRequestError(HTTPError):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "Bad Request Error"


class NotFoundError(HTTPError):
    status_code = HTTPStatus.NOT_FOUND
    detail = "Not Found Error"


class MethodNotAllowedError(HTTPError):
    status_code = HTTPStatus.METHOD_NOT_ALLOWED
    detail = "Method Not Allowed Error"


class TooManyRequestsError(HTTPError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    detail = "Too Many Requests Error"