from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import requests

class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keycloak_endpoint_url = "https://dev.loginproxy.gov.bc.ca/auth/realms/standard/protocol/openid-connect/userinfo"
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Extract bearer token from the request headers
            authorization_header = request.headers.get('Authorization')
            if not authorization_header or not authorization_header.startswith('Bearer '):
                raise HTTPException(status_code=401, detail="Unauthorized")
            token = authorization_header.split(' ')[1]
            
            # Set up the headers with the bearer token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Make a GET request to the Keycloak endpoint
            response = requests.get(self.keycloak_endpoint_url, headers=headers)
            
            # Check the response
            if response.status_code == 200:
                # Authentication successful, proceed to the next middleware or endpoint handler
                return await call_next(request)
            else:
                # Authentication failed, raise HTTPException
                raise HTTPException(status_code=401, detail="Unauthorized")
        except Exception as e:
            raise HTTPException(status_code=401, detail="Unauthorized")