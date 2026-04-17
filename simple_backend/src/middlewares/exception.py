from starlette.responses import JSONResponse

from src.utils.error import Error


class GlobalExceptionHandlerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].startswith("/mcp"):
            return await self.app(scope, receive, send)

        try:
            await self.app(scope, receive, send)
        except Error as e:
            response = JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "message": e.message,
                    "detail": e.detail,
                },
            )
            await response(scope, receive, send)
        except Exception:
            response = JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Unexpected error occurred.",
                },
            )
            await response(scope, receive, send)