from fastapi import Header, HTTPException, Depends
from app.middleware.authentication import AuthenticationMiddleware

async def get_user_info(user_info: dict = Depends(AuthenticationMiddleware)):
    return user_info