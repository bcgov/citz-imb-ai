from fastmcp import FastMCP
from typing import Dict, List, Optional
import os
import importlib.util


class AgentRegistry:
    """Central registry for all MCP agents with auto-discovery capabilities"""
    
    def __init__(self):
        self._agents: Dict[str, FastMCP] = {}
        self._orchestrator: Optional[FastMCP] = None
        self._capabilities: Dict[str, List[str]] = {}
        self._discover_agents()
    
    def _discover_agents(self):
        """Auto-discover all agents in subdirectories"""
        # Import search agents
        from .search.semantic_search import semantic_search_mcp
        from .search.explicit_search import explicit_search_mcp
        from .search.community_detection import community_detection_mcp
        
        # Register search agents
        self._agents["semantic_search"] = semantic_search_mcp
        self._agents["explicit_search"] = explicit_search_mcp
        self._agents["community_detection"] = community_detection_mcp
        
        # Define capabilities
        self._capabilities["search"] = ["semantic_search", "explicit_search", "community_detection"]
    
    def get_agent(self, name: str) -> Optional[FastMCP]:
        """Get a specific agent by name"""
        return self._agents.get(name)
    
    def get_agents_by_capability(self, capability: str) -> List[FastMCP]:
        """Get all agents that have a specific capability"""
        agent_names = self._capabilities.get(capability, [])
        return [self._agents[name] for name in agent_names if name in self._agents]
    
    def list_agents(self) -> List[str]:
        """List all available agent names"""
        return list(self._agents.keys())
    
    def list_capabilities(self) -> List[str]:
        """List all available capabilities"""
        return list(self._capabilities.keys())
    
    def create_main_server(self) -> FastMCP:
        """Create the main aggregated MCP server"""
        main_server = FastMCP(name="MainAgentServer")
        
        # Mount search agents
        for agent_name, agent in self._agents.items():
            if agent_name in self._capabilities.get("search", []):
                prefix = agent_name.replace("_", "")
                main_server.mount(agent, prefix=prefix)
        
        return main_server
    
    def get_combined_mcp(self) -> FastMCP:
        """Get the combined MCP server with all agents"""
        return self.create_main_server()


# Create global registry instance
agent_registry = AgentRegistry()

# Create the main server for backward compatibility
agents_mcp = agent_registry.create_main_server()

__all__ = ["agent_registry", "agents_mcp"]
