from typing import List
from pydantic import BaseModel


class ChatHistory(BaseModel):
    prompt: str
    response: str


class ChatRequest(BaseModel):
    prompt: str
    chatHistory: List[ChatHistory]
    key: str
