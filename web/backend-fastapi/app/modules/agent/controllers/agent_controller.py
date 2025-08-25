from fastapi import APIRouter, Depends
from ..services.agent_service import AgentService
from ..services.orchestrator_service import OrchestratorService
from ..views.agent_views import AgentViews
from ..models.agent_model import AgentRequest, OrchestrationRequest
from app.shared.utils.user_utils import get_user_info


class AgentController:
    def __init__(self):
        self.router = APIRouter()
        self.agent_service = AgentService()
        self.orchestrator_service = OrchestratorService()
        self.agent_views = AgentViews()
        self._setup_routes()

    def _setup_routes(self):
        """Setup all agent routes"""

        @self.router.post("/agent/")
        async def agentic_chat(
            request: AgentRequest = None, user: str = Depends(get_user_info)
        ):
            result = await self.agent_service.process_agent_chat(request, user)
            return self.agent_views.agent_response(result)

        @self.router.post("/agent/orchestrate/")
        async def orchestrate_task(request: OrchestrationRequest):
            """Orchestrate complex multi-agent tasks"""
            agent_request = AgentRequest(prompt=request.task)
            result = await self.orchestrator_service.orchestrate_complex_task(
                agent_request, request.required_capabilities, request.execution_strategy
            )
            return self.agent_views.agent_response(result)

        @self.router.get("/agent/capabilities/")
        async def get_orchestration_capabilities():
            """Get available orchestration capabilities and agents"""
            result = await self.orchestrator_service.get_orchestration_capabilities()
            return result

        @self.router.get("/agent/status/{agent_name}")
        async def get_agent_status(agent_name: str):
            """Get the status of a specific agent"""
            result = await self.orchestrator_service.get_agent_status(agent_name)
            return result


# Create router instance
agent_controller = AgentController()
router = agent_controller.router
