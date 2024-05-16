from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import requests
from requests.exceptions import RequestException
from fastapi.responses import JSONResponse

class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keycloak_endpoint_url = "https://dev.loginproxy.gov.bc.ca/auth/realms/standard/protocol/openid-connect/userinfo"
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Extract bearer token from the request headers
            url_path = str(request.url).split('/')[-1]
            if (url_path == "docs"  or url_path == "openapi.json"):
                return await call_next(request)
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
        except RequestException as e:
            # Handle request-related exceptions
            raise HTTPException(status_code=503, detail="Service Unavailable")
        except HTTPException as e:
            # Handle specific HTTPException gracefully
            if e.status_code == 401:
                return JSONResponse(status_code=401, content={"detail": "Authentication required"})
            else:
                # Re-raise HTTPException with the same status code and detail
                raise e
        except Exception as e:
            # Catch any other unexpected exceptions and return a generic error
            #return await call_next(request)
            return JSONResponse(status_code=401, content={"detail": f"error: {e}"})
            #raise HTTPException(status_code=500, detail="Internal Server Error")