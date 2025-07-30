from fastapi import APIRouter, Body
from ..services.chat_service import ChatService
from ..views.chat_views import ChatViews
from ..models.chat_model import ChatRequest


class ChatController:
    def __init__(self):
        self.router = APIRouter()
        self.chat_service = ChatService()
        self.chat_views = ChatViews()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all chat routes"""
        
        @self.router.post("/chat/")
        async def chat(chat_request: ChatRequest = Body(ChatRequest)):
            result = await self.chat_service.process_chat(chat_request)
            return self.chat_views.chat_response(result)
        
        @self.router.get("/chat/states/")
        async def get_states():
            result = await self.chat_service.get_available_states()
            return self.chat_views.states_response(result)


# Create router instance
chat_controller = ChatController()
router = chat_controller.router