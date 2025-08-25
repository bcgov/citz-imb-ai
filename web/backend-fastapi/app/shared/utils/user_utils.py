from fastapi import Request, HTTPException
from typing import List


class UserInfo:
    """
    Class-based dependency for user information.
    Can be used with FastAPI Depends for a more object-oriented approach.

    Usage:
        @router.get("/endpoint")
        async def my_endpoint(user: UserInfo = Depends(UserInfo)):
            user_id = user.id
            roles = user.roles
    """

    def __init__(self, request: Request):
        """
        Initialize UserInfo with request context.
        FastAPI will automatically inject the Request when used with Depends.
        """
        self.request = request
        self._load_user_data()

    def _load_user_data(self):
        """Load user data from request state"""
        self._user_id = getattr(self.request.state, "user_id", None)
        self._user_roles = getattr(self.request.state, "user_roles", None)

        if self._user_id is None:
            raise HTTPException(status_code=401, detail="User not authenticated")

    @property
    def id(self) -> str:
        """Get the user ID"""
        return self._user_id

    @property
    def roles(self) -> List[str]:
        """Get the user roles"""
        return self._user_roles or []

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles

    def has_any_role(self, required_roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in required_roles)

    def __str__(self) -> str:
        """String representation"""
        return f"UserInfo(id={self.id}, roles={self.roles})"
