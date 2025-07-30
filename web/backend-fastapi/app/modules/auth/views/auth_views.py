from fastapi.responses import JSONResponse
from ..models.auth_model import LoginResponse, ValidationResponse, TokenResponse, HealthResponse


class AuthViews:
    @staticmethod
    def login_response(data: LoginResponse) -> JSONResponse:
        """Format login response"""
        return JSONResponse(content=data.dict())
    
    @staticmethod
    def validation_response(data: ValidationResponse) -> JSONResponse:
        """Format validation response"""
        return JSONResponse(content=data.dict())
    
    @staticmethod
    def token_response(data: TokenResponse) -> dict:
        """Format token refresh response"""
        return data.dict()
    
    @staticmethod
    def health_response(data: dict) -> dict:
        """Format health check response"""
        return data
    
    @staticmethod
    def main_response() -> dict:
        """Format main endpoint response"""
        return {"msg": "Hello World"}