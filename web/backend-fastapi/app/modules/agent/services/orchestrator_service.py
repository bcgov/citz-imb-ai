import os
import json
from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from fastapi.logger import logger
from fastmcp import Client
from fastmcp.exceptions import ToolError

from ..agents import agent_registry
from ..agents.orchestrator.orchestrator_agent import orchestrator_mcp
from app.shared.models.azure import AzureAI
from ..models.agent_model import AgentRequest, AgentResponse


class OrchestratorService:
    """High-level orchestration service for managing complex multi-agent tasks"""
    
    def __init__(self):
        self.azure_endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
        self.azure_key = os.getenv("AZURE_AI_KEY", "")
        self.max_iterations = 10
    
    async def orchestrate_complex_task(
        self, 
        request: AgentRequest,
        capabilities: Optional[List[str]] = None,
        strategy: str = "adaptive"
    ) -> AgentResponse:
        """
        Orchestrate a complex task using multiple agents
        
        Args:
            request: The agent request containing the task
            capabilities: Optional list of required capabilities
            strategy: Execution strategy ("parallel", "sequential", "adaptive")
        """
        logger.info(f"Orchestrating complex task: {request.prompt}")
        
        # Azure Configuration for high-level orchestration
        azure = AzureAI(self.azure_endpoint, self.azure_key)
        
        try:
            # Establish connection to orchestrator
            client = Client(orchestrator_mcp)
            async with client:
                # Get orchestrator tools
                raw_tools = await client.list_tools()
                tools = [
                    {
                        "type": "function", 
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                    for tool in raw_tools
                ]
                
                # Add orchestration context
                orchestration_context = self._get_orchestration_context(capabilities, strategy)
                azure.add_system_message(orchestration_context)
                
                # Process with orchestrator
                response = azure.call_agent_with_history(request.prompt, tools=tools)
                
                # Handle tool calls for orchestration
                finish_reason = response.get("finish_reason")
                current_iteration = 0
                
                while finish_reason != "stop" and current_iteration < self.max_iterations:
                    if finish_reason == "tool_calls":
                        tool_calls = response.get("message").get("tool_calls")
                        for tool_call in tool_calls:
                            tool_call_id = tool_call.get("id")
                            tool_name = tool_call.get("function").get("name")
                            arguments_str = tool_call.get("function").get("arguments")
                            
                            try:
                                arguments = json.loads(arguments_str)
                                logger.info(f"Orchestrator calling tool: {tool_name} with {arguments}")
                                
                                result = await client.call_tool(tool_name, arguments)
                                logger.info(f"Orchestrator tool {tool_name} returned: {result}")
                                azure.add_tool_response(tool_call_id, result)
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"Error parsing orchestrator arguments: {e}")
                                continue
                            except ToolError as tool_error:
                                error_message = f"Orchestrator tool error in {tool_name}: {str(tool_error)}"
                                logger.error(error_message)
                                azure.add_tool_response(tool_call_id, {"error": error_message})
                            except Exception as e:
                                error_message = f"Unexpected orchestrator error in {tool_name}: {str(e)}"
                                logger.error(error_message)
                                azure.add_tool_response(tool_call_id, {"error": error_message})
                        
                        # Continue orchestration conversation
                        response = azure.call_agent_with_history("", tools=tools, role="user")
                        finish_reason = response.get("finish_reason")
                        current_iteration += 1
                        
                    elif finish_reason == "length":
                        logger.warning("Orchestration length exceeded limit. Stopping.")
                        break
                    else:
                        logger.warning(f"Unexpected orchestration finish reason: {finish_reason}")
                        break
                
                response_text = response.get("message").get("content", "").strip()
                return AgentResponse(response=response_text, history=azure.history)
                
        except Exception as e:
            logger.error("Error during orchestration:", exc_info=True)
            raise e
    
    async def get_orchestration_capabilities(self) -> Dict[str, Any]:
        """Get available orchestration capabilities and agents"""
        try:
            client = Client(orchestrator_mcp)
            async with client:
                result = await client.call_tool("list_agent_capabilities", {})
                return result
        except Exception as e:
            logger.error(f"Error getting orchestration capabilities: {e}")
            return {"error": str(e)}
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of a specific agent"""
        try:
            client = Client(orchestrator_mcp)
            async with client:
                result = await client.call_tool("get_agent_status", {"agent_name": agent_name})
                return result
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {"error": str(e)}
    
    def _get_orchestration_context(self, capabilities: Optional[List[str]], strategy: str) -> str:
        """Create orchestration context for the Azure AI"""
        context = f"""
        You are a high-level AI orchestrator that coordinates multiple specialized agents to complete complex tasks.
        
        Available agent capabilities: {agent_registry.list_capabilities()}
        Available agents: {agent_registry.list_agents()}
        
        Your role is to:
        1. Analyze complex user requests
        2. Determine which specialized agents are needed
        3. Coordinate multiple agents to work together
        4. Synthesize results into cohesive responses
        
        Execution strategy: {strategy}
        """
        
        if capabilities:
            context += f"\nRequired capabilities for this task: {capabilities}"
        
        context += """
        
        Use the orchestration tools available to:
        - orchestrate_task: Plan and coordinate complex multi-agent tasks
        - list_agent_capabilities: See what agents and capabilities are available
        - get_agent_status: Check the status of specific agents
        
        Always provide clear, actionable orchestration plans and coordinate agents effectively.
        """
        
        return context