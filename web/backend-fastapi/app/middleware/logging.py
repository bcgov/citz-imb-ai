import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log the request method and path
        logging.info(f"Request: {request.method} {request.url.path}")
        
        # Proceed to the next middleware or endpoint handler
        response = await call_next(request)
        
        # Log the response status code
        logging.info(f"Response: {response.status_code}")
        
        return response