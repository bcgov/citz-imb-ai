from fastapi import APIRouter, Form, Depends
from ..services.auth_service import AuthService
from ..views.auth_views import AuthViews
from ..models.auth_model import TokenRequest


class AuthController:
    def __init__(self):
        self.router = APIRouter()
        self.auth_service = AuthService()
        self.auth_views = AuthViews()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all authentication routes"""
        
        @self.router.get("/")
        async def read_main():
            return self.auth_views.main_response()
        
        @self.router.get("/login")
        async def login():
            result = await self.auth_service.login()
            return self.auth_views.login_response(result)
        
        @self.router.get("/validate")
        async def validate():
            result = await self.auth_service.validate_user()
            return self.auth_views.validation_response(result)
        
        @self.router.post("/refreshtoken/")
        async def refresh_token(refresh_token: str = Form(...)):
            result = await self.auth_service.refresh_token(refresh_token)
            return self.auth_views.token_response(result)
        
        @self.router.get("/health")
        async def health_check():
            result = await self.auth_service.health_check()
            return self.auth_views.health_response(result)


# Create router instance
auth_controller = AuthController()
router = auth_controller.router