from fastmcp import FastMCP
from typing import Dict, List, Any, Optional
import json
from fastapi.logger import logger

# Import registry to access sub-agents
from .. import agent_registry

orchestrator_mcp = FastMCP(name="OrchestratorAgent")


@orchestrator_mcp.tool(
    name="orchestrate_task",
    description="""High-level orchestrator that can deploy and coordinate multiple specialized agents to complete complex tasks.
    
    This agent can:
    - Analyze task requirements and determine which specialized agents are needed
    - Coordinate multiple agents to work together on complex queries
    - Combine results from different agents into cohesive responses
    - Route tasks to the most appropriate specialized agents
    """
)
def orchestrate_task(
    task: str,
    required_capabilities: Optional[List[str]] = None,
    execution_strategy: str = "parallel"
) -> Dict[str, Any]:
    """
    Orchestrate a complex task using multiple specialized agents
    
    Args:
        task: The high-level task to complete
        required_capabilities: List of capabilities needed (e.g., ["search", "analysis"])
        execution_strategy: How to execute subtasks ("parallel", "sequential", "adaptive")
    
    Returns:
        Dict containing orchestrated response and execution details
    """
    logger.info(f"Orchestrator received task: {task}")
    
    # If no capabilities specified, analyze the task to determine what's needed
    if not required_capabilities:
        required_capabilities = _analyze_task_requirements(task)
    
    logger.info(f"Required capabilities: {required_capabilities}")
    
    # Get available agents for each capability
    available_agents = {}
    for capability in required_capabilities:
        agents = agent_registry.get_agents_by_capability(capability)
        available_agents[capability] = [agent.name for agent in agents]
    
    # Create execution plan
    execution_plan = _create_execution_plan(task, required_capabilities, execution_strategy)
    
    # For now, return a structured response indicating orchestration capability
    # Future implementation will actually execute the plan
    response = {
        "orchestrator_response": f"Task '{task}' analyzed and ready for execution",
        "required_capabilities": required_capabilities,
        "available_agents": available_agents,
        "execution_plan": execution_plan,
        "execution_strategy": execution_strategy,
        "status": "planned",
        "next_steps": [
            "Execute sub-tasks using specialized agents",
            "Combine and synthesize results",
            "Return unified response"
        ]
    }
    
    logger.info(f"Orchestration plan created: {response}")
    return response


@orchestrator_mcp.tool(
    name="list_agent_capabilities",
    description="List all available agent capabilities and the agents that provide them"
)
def list_agent_capabilities() -> Dict[str, Any]:
    """
    List all available capabilities and agents
    
    Returns:
        Dict containing capabilities and agent mappings
    """
    capabilities = {}
    for capability in agent_registry.list_capabilities():
        agents = agent_registry.get_agents_by_capability(capability)
        capabilities[capability] = [agent.name for agent in agents]
    
    return {
        "available_capabilities": capabilities,
        "total_agents": len(agent_registry.list_agents()),
        "agent_list": agent_registry.list_agents()
    }


@orchestrator_mcp.tool(
    name="get_agent_status",
    description="Get the status and capabilities of a specific agent"
)
def get_agent_status(agent_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific agent
    
    Args:
        agent_name: Name of the agent to query
        
    Returns:
        Dict containing agent status and capabilities
    """
    agent = agent_registry.get_agent(agent_name)
    
    if not agent:
        return {
            "status": "not_found",
            "message": f"Agent '{agent_name}' not found",
            "available_agents": agent_registry.list_agents()
        }
    
    return {
        "status": "active",
        "agent_name": agent_name,
        "agent_type": agent.name,
        "capabilities": _get_agent_capabilities(agent_name),
        "tools_available": len(getattr(agent, 'tools', [])) if hasattr(agent, 'tools') else 0
    }


def _analyze_task_requirements(task: str) -> List[str]:
    """
    Analyze a task to determine what capabilities are needed
    
    This is a simple implementation - can be enhanced with AI/ML
    """
    task_lower = task.lower()
    capabilities = []
    
    # Check for search-related keywords
    search_keywords = ["search", "find", "look", "query", "retrieve", "get information"]
    if any(keyword in task_lower for keyword in search_keywords):
        capabilities.append("search")
    
    # Add more capability detection logic here
    # if any(keyword in task_lower for keyword in analysis_keywords):
    #     capabilities.append("analysis")
    
    # Default to search if no specific capability detected
    if not capabilities:
        capabilities.append("search")
    
    return capabilities


def _create_execution_plan(task: str, capabilities: List[str], strategy: str) -> List[str]:
    """
    Create a detailed execution plan for the task
    """
    plan = []
    
    for capability in capabilities:
        agents = agent_registry.get_agents_by_capability(capability)
        if agents:
            if strategy == "parallel":
                plan.append(f"Execute {capability} tasks in parallel using: {[a.name for a in agents]}")
            elif strategy == "sequential":
                plan.append(f"Execute {capability} tasks sequentially using: {[a.name for a in agents]}")
            else:  # adaptive
                plan.append(f"Adaptively execute {capability} tasks using best available agent")
    
    plan.append("Synthesize results from all agents")
    plan.append("Return unified response to user")
    
    return plan


def _get_agent_capabilities(agent_name: str) -> List[str]:
    """
    Get the capabilities provided by a specific agent
    """
    for capability, agent_names in agent_registry._capabilities.items():
        if agent_name in agent_names:
            return [capability]
    return []
