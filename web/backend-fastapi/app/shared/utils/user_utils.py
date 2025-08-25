from fastapi import Request, HTTPException


def get_user_info(request: Request) -> dict:
    """
    Dependency to get both user ID and roles from the request state.

    Returns:
        dict: Dictionary containing 'user_id' and 'user_roles'

    Raises:
        HTTPException: If user information is not found (user not authenticated)
    """
    user_id = getattr(request.state, "user_id", None)
    user_roles = getattr(request.state, "user_roles", None)

    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    return {"id": user_id, "roles": user_roles}
