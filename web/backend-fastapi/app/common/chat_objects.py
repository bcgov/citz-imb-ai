from typing import List, Optional
from pydantic import BaseModel


class ChatHistory(BaseModel):
    prompt: str
    response: str


class ChatRequest(BaseModel):
    prompt: str
    chatHistory: List[ChatHistory]
    key: Optional[str] = None
