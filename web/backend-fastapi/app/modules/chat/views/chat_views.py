from typing import List
from ..models.chat_model import ChatResponse, StateResponse


class ChatViews:
    @staticmethod
    def chat_response(data: ChatResponse) -> dict:
        """Format chat response"""
        return data.dict()
    
    @staticmethod
    def states_response(data: StateResponse) -> List[dict]:
        """Format states response"""
        return data.states
