import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import requests
from requests.exceptions import RequestException
import os


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keycloak_endpoint_url = "https://dev.loginproxy.gov.bc.ca/auth/realms/standard/protocol/openid-connect/userinfo"
        self.load_roles()

    def load_roles(self):
        # Get the directory of the current file
        current_dir = os.path.dirname(__file__)
        # Construct the path to the roles.json file
        roles_file_path = os.path.join(current_dir, "..", "roles.json")
        # Load the roles from the JSON file
        with open(roles_file_path) as f:
            self.allowed_roles = json.load(f).get("roles", [])

    async def dispatch(self, request: Request, call_next):
        try:
            # Extract bearer token from the request headers
            url_path = str(request.url).split("/")[-1]
            if url_path in ("docs", "openapi.json", "health"):
                return await call_next(request)

            authorization_header = request.headers.get("Authorization")
            if not authorization_header or not authorization_header.startswith(
                "Bearer "
            ):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

            token = authorization_header.split(" ")[1]

            # Set up the headers with the bearer token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # Make a GET request to the Keycloak endpoint
            response = requests.get(self.keycloak_endpoint_url, headers=headers)

            # Check the response
            if response.status_code == 200:
                user_info = response.json()
                user_roles = user_info.get("client_roles", [])

                if not any(role in self.allowed_roles for role in user_roles):
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Forbidden: You do not have the required roles"
                        },
                    )
                # Add user info to request state for downstream use
                request.state.user_id = user_info.get("sub").split("@")[0]
                request.state.user_roles = user_roles
                # Authentication and role validation successful, proceed to the next middleware or endpoint handler
                return await call_next(request)
            else:
                # Authentication failed, raise HTTPException
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        except RequestException:
            # Handle request-related exceptions
            return JSONResponse(
                status_code=503, content={"detail": "Service Unavailable"}
            )

        except HTTPException as e:
            # Handle specific HTTPException gracefully
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

        except Exception as e:
            # Catch any other unexpected exceptions and return a generic error
            return JSONResponse(status_code=500, content={"detail": f"error: {e}"})
