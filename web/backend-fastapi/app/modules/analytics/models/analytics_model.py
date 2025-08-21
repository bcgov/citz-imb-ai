from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class AnalyticsData(BaseModel):
    sessionId: str
    chats: Optional[List[Dict[str, Any]]] = []
    metadata: Optional[Dict[str, Any]] = {}


class AnalyticsUpdate(BaseModel):
    sessionId: str
    newChat: Optional[Dict[str, Any]] = None
    sourceUpdate: Optional[Dict[str, Any]] = None
    llmResponseUpdate: Optional[Dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    message: str
    status: str = "success"
