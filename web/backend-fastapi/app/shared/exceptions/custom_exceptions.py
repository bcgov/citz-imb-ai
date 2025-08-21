from fastapi import HTTPException
from typing import Optional, Any


class ModuleException(HTTPException):
    """Base exception for module-specific errors"""
    
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        module: str = "Unknown",
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.module = module


class AuthenticationError(ModuleException):
    """Authentication module specific error"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail, module="auth")


class ChatError(ModuleException):
    """Chat module specific error"""
    
    def __init__(self, detail: str = "Chat processing error", status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail, module="chat")


class AgentError(ModuleException):
    """Agent module specific error"""
    
    def __init__(self, detail: str = "Agent processing error", status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail, module="agent")


class AnalyticsError(ModuleException):
    """Analytics module specific error"""
    
    def __init__(self, detail: str = "Analytics processing error", status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail, module="analytics")


class FeedbackError(ModuleException):
    """Feedback module specific error"""
    
    def __init__(self, detail: str = "Feedback processing error", status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail, module="feedback")
