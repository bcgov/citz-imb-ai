from fastmcp import FastMCP

# 1. Import the individual MCP server instances from agent files
from app.mcp_agents.semantic_search import semantic_search_mcp
from app.mcp_agents.community_detection import community_detection_mcp

# 2. Create the main, aggregated MCP server that clients will connect to
agents_mcp = FastMCP(name="MainAgentServer")

# 3. Mount each individual agent server onto the main one with a prefix.
#    This makes their tools available under names like 'semanticsearch_search'
agents_mcp.mount(semantic_search_mcp, prefix="semanticsearch")
agents_mcp.mount(community_detection_mcp, prefix="communitydetection")
