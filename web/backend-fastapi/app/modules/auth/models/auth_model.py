from pydantic import BaseModel
from typing import Optional


class TokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


class LoginResponse(BaseModel):
    valid: bool
    message: Optional[str] = None


class ValidationResponse(BaseModel):
    status: str
    user_id: Optional[str] = None
    roles: Optional[list] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: Optional[str] = None
