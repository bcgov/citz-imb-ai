from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional


class ResponseUtils:
    """Utility class for standardized API responses"""
    
    @staticmethod
    def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Standard success response format"""
        return {
            "status": "success",
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error_response(message: str, code: str = "ERROR") -> Dict[str, Any]:
        """Standard error response format"""
        return {
            "status": "error",
            "message": message,
            "code": code
        }
    
    @staticmethod
    def json_response(data: Any, status_code: int = 200) -> JSONResponse:
        """Create JSONResponse with standard format"""
        return JSONResponse(content=data, status_code=status_code)