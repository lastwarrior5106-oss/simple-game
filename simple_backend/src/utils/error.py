import sys
import types
from http import HTTPStatus
from typing import List, Union

from src.utils.common import json_serializer


class Error(Exception):
    message: str = "Unexpected error occurred."
    status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str = None,
        *,
        detail: dict = None,
        caught_exception: Exception = None,
    ) -> None:
        if message is not None:
            self.message = message

        self.detail = detail or {}
        self.caught_exception = caught_exception or sys.exc_info()[1]

    @property
    def __dict__(self):
        detail = self.detail or ""
        caught_exception: dict = {}

        if self.caught_exception:
            caught_exception["name"] = getattr(type(self.caught_exception), "__name__", "")
            caught_exception["repr"] = getattr(self.caught_exception, "__repr__", lambda x: "")()

        return {
            "detail": detail,
            "caught_exception": caught_exception,
        }

    def __str__(self):
        return json_serializer({"message": self.message, **self.__dict__})

    def with_current_traceback(self, ignored_packages: Union[List, None] = None):
        tb = None

        if ignored_packages is None:
            ignored_packages = [
                "fastapi.",
                "starlette.",
                "uvicorn.",
                "multiprocessing.",
                "asyncio.",
                "algo_utils.error",
            ]

        frame = sys._getframe()

        while frame is not None:
            try:
                module = frame.f_globals["__name__"]
                if any(module.startswith(ignored) for ignored in ignored_packages):
                    frame = frame.f_back
                    continue
            except (AttributeError, KeyError):
                pass

            tb = types.TracebackType(tb, frame, frame.f_lasti, frame.f_lineno)
            frame = frame.f_back

        return self.with_traceback(tb)


class BadRequestError(Error):
    message = "Bad request"
    status_code = HTTPStatus.BAD_REQUEST


class ValidationError(Error):
    message = "Validation error"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class UnauthorizedError(Error):
    message = "Unauthorized"
    status_code = HTTPStatus.UNAUTHORIZED


class ForbiddenError(Error):
    message = "Forbidden"
    status_code = HTTPStatus.FORBIDDEN


class NotFoundError(Error):
    message = "Not found"
    status_code = HTTPStatus.NOT_FOUND


class ConflictError(Error):
    message = "Conflict"
    status_code = HTTPStatus.CONFLICT