from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid


class AgentRequest(BaseModel):
    prompt: str
    chat_id: Optional[str] = None


# Includes chat_id as uuid
class AgentResponse(BaseModel):
    response: str
    history: List[Dict[str, Any]]
    chat_id: uuid.UUID
    chat_title: str


class DatabaseSchema(BaseModel):
    schema_info: str
    labels: List[str]


# New orchestration models
class AgentCapability(BaseModel):
    name: str
    description: str
    agents: List[str]


class OrchestrationRequest(BaseModel):
    task: str
    required_capabilities: Optional[List[str]] = None
    execution_strategy: str = "adaptive"
    priority: Optional[str] = "normal"


class OrchestrationResponse(BaseModel):
    orchestrator_response: str
    required_capabilities: List[str]
    available_agents: Dict[str, List[str]]
    execution_plan: List[str]
    execution_strategy: str
    status: str


class AgentStatusResponse(BaseModel):
    status: str
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tools_available: Optional[int] = None
    message: Optional[str] = None
