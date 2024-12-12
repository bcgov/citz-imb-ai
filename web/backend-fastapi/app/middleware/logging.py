import logging
from fastapi import Request
from fastapi.logger import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        gunicorn_logger = logging.getLogger("gunicorn.error")
        logger.handlers = gunicorn_logger.handlers
        if __name__ != "main":
            logger.setLevel(gunicorn_logger.level)
        else:
            logger.setLevel(logging.DEBUG)
        # Log the request method and path
        logger.info(f"Request: {request.method} {request.url.path}")

        # Proceed to the next middleware or endpoint handler
        response = await call_next(request)

        # Log the response status code
        logger.info(f"Response: {response.status_code}")

        return response
