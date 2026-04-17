import time
import uuid

from loguru import logger


class RequestLoggerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].startswith("/mcp"):
            return await self.app(scope, receive, send)

        request_id = str(uuid.uuid4())
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]

        logger.info(f"[{request_id}] {method} {path} - started")

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                logger.info(
                    f"[{request_id}] {method} {path} - "
                    f"status={message['status']} duration={process_time:.4f}s"
                )
            await send(message)

        scope["request_id"] = request_id
        await self.app(scope, receive, wrapped_send)