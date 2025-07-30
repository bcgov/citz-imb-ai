from ..models.agent_model import AgentResponse


class AgentViews:
    @staticmethod
    def agent_response(data: AgentResponse) -> dict:
        """Format agent response"""
        return data.dict()