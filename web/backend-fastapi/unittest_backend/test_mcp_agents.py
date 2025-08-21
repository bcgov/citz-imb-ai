import unittest
import asyncio
from unittest.mock import patch, MagicMock
from fastmcp import Client

# Import your agents
from app.modules.agent.agents import agent_registry
from app.modules.agent.agents.search.semantic_search import semantic_search_mcp
from app.modules.agent.agents.search.explicit_search import explicit_search_mcp
from app.modules.agent.agents.search.community_detection import community_detection_mcp


class TestMCPAgents(unittest.TestCase):
    """Test individual MCP agents"""
    
    def test_agent_registry_initialization(self):
        """Test that agent registry initializes correctly"""
        agents = agent_registry.list_agents()
        self.assertIn("semantic_search", agents)
        self.assertIn("explicit_search", agents)
        self.assertIn("community_detection", agents)
        
        capabilities = agent_registry.list_capabilities()
        self.assertIn("search", capabilities)
    
    def test_get_agent_by_name(self):
        """Test retrieving specific agents"""
        semantic_agent = agent_registry.get_agent("semantic_search")
        self.assertIsNotNone(semantic_agent)
        self.assertEqual(semantic_agent.name, "SemanticSearchAgent")
        
        explicit_agent = agent_registry.get_agent("explicit_search")
        self.assertIsNotNone(explicit_agent)
        
        # Test non-existent agent
        nonexistent = agent_registry.get_agent("nonexistent")
        self.assertIsNone(nonexistent)
    
    def test_get_combined_mcp(self):
        """Test that combined MCP server is created"""
        combined_mcp = agent_registry.get_combined_mcp()
        self.assertIsNotNone(combined_mcp)
        self.assertEqual(combined_mcp.name, "MainAgentServer")


class TestMCPAgentTools(unittest.TestCase):
    """Test MCP agent tools using direct client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up after tests"""
        self.loop.close()
    
    @patch('app.shared.models.neo4j.neo4j')
    @patch('app.shared.models.rag.get_full_rag')
    def test_semantic_search_tool(self, mock_rag, mock_neo4j):
        """Test semantic search tool"""
        # Mock the RAG response
        mock_rag.return_value.query.return_value = [
            {"content": "Test result 1"},
            {"content": "Test result 2"}
        ]
        
        async def run_test():
            client = Client(semantic_search_mcp)
            async with client:
                # List tools
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                self.assertIn("semantic_search", tool_names)
                
                # Call the tool
                result = await client.call_tool("semantic_search", {
                    "query": "test query",
                    "state_key": "v3"
                })
                
                self.assertIsInstance(result, dict)
                # Verify RAG was called
                mock_rag.return_value.query.assert_called_once()
        
        self.loop.run_until_complete(run_test())
    
    @patch('app.shared.models.neo4j.neo4j')
    def test_explicit_search_tool(self, mock_neo4j):
        """Test explicit search tool"""
        # Mock Neo4j response
        mock_neo4j_instance = MagicMock()
        mock_neo4j_instance.query.return_value = [
            {"name": "Test Document", "content": "Test content"}
        ]
        mock_neo4j.return_value = mock_neo4j_instance
        
        async def run_test():
            client = Client(explicit_search_mcp)
            async with client:
                # List tools
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                self.assertIn("explicit_search", tool_names)
                
                # Call the tool
                result = await client.call_tool("explicit_search", {
                    "query": "SELECT * FROM Document LIMIT 5",
                    "state_key": "v3"
                })
                
                self.assertIsInstance(result, dict)
                # Verify Neo4j was called
                mock_neo4j_instance.query.assert_called_once()
        
        self.loop.run_until_complete(run_test())
    
    def test_combined_mcp_tools(self):
        """Test combined MCP server has all tools"""
        async def run_test():
            combined_mcp = agent_registry.get_combined_mcp()
            client = Client(combined_mcp)
            
            async with client:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                
                # Should have tools from all mounted agents
                expected_tools = [
                    "semanticsearch_semantic_search",
                    "explicitsearch_explicit_search", 
                    "communitydetection_community_detection"
                ]
                
                for expected_tool in expected_tools:
                    self.assertIn(expected_tool, tool_names)
        
        self.loop.run_until_complete(run_test())


class TestMCPServerHealth(unittest.TestCase):
    """Test MCP server health and connectivity"""
    
    def test_agent_mcp_servers_exist(self):
        """Test that all MCP server instances exist"""
        self.assertIsNotNone(semantic_search_mcp)
        self.assertIsNotNone(explicit_search_mcp)
        self.assertIsNotNone(community_detection_mcp)
        
        # Test server names
        self.assertEqual(semantic_search_mcp.name, "SemanticSearchAgent")
        self.assertEqual(explicit_search_mcp.name, "ExplicitSearchAgent")
        self.assertEqual(community_detection_mcp.name, "CommunityDetectionAgent")
    
    def test_server_tool_registration(self):
        """Test that tools are properly registered on servers"""
        # Each server should have exactly one tool
        self.assertEqual(len(semantic_search_mcp._tools), 1)
        self.assertEqual(len(explicit_search_mcp._tools), 1)
        self.assertEqual(len(community_detection_mcp._tools), 1)
        
        # Check tool names
        self.assertIn("semantic_search", semantic_search_mcp._tools)
        self.assertIn("explicit_search", explicit_search_mcp._tools)
        self.assertIn("community_detection", community_detection_mcp._tools)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
