import requests
import os
from fastapi import HTTPException
from ..models.auth_model import TokenResponse, LoginResponse, ValidationResponse


class AuthService:
    def __init__(self):
        self.keycloak_endpoint = 'https://dev.loginproxy.gov.bc.ca/auth/realms/standard/protocol/openid-connect/token'
        self.client_id = 'a-i-pathfinding-project-5449'
    
    async def login(self) -> LoginResponse:
        """Handle user login - returns basic validation"""
        return LoginResponse(valid=True)
    
    async def validate_user(self) -> ValidationResponse:
        """Validate user session"""
        return ValidationResponse(status="ok")
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh user token using Keycloak"""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        try:
            response = requests.post(self.keycloak_endpoint, headers=headers, data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail="Token refresh failed"
                )
            
            token_data = response.json()
            return TokenResponse(
                access_token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                expires_in=token_data.get('expires_in'),
                token_type=token_data.get('token_type', 'Bearer')
            )
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")
    
    async def health_check(self):
        """Check service health"""
        return {"status": "healthy"}