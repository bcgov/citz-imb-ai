# Agentic Flow

This diagram represents a simplified sequence where an AI Agent can utilize MCP tools at its descretion.

The initial set of tools are obtained from the MCP Server and provided to the AI Agent. The AI Agent can then decide to use one or many of these tools to gain additional context for its final response.

It was used in an initial version of the agentic workflow.

```mermaid
sequenceDiagram
  participant Client as Client
  participant agentic_chat as FastAPI
  participant AzureAI as AI Agent (Azure)
  participant MCP_Client as MCP Server
  participant database as Database

  Client ->> agentic_chat: POST request with query
  agentic_chat ->> AzureAI: Create AzureAI instance
  agentic_chat ->> MCP_Client: Connect to MCP Server
  agentic_chat ->> MCP_Client: Request Tool List
  MCP_Client -->> agentic_chat: Receive Tool List
  agentic_chat ->> agentic_chat: Convert tools to Azure format
  agentic_chat ->> database: Request Database Schema
  database ->> agentic_chat: Return Database Schema
  agentic_chat ->> AzureAI: Set Initial Agent Context
  agentic_chat ->> AzureAI: Send Query with Tools List
  AzureAI -->> agentic_chat: Receive response w/ Finish Reason
  loop While Finish Reason != "stop": Continue to Prompt AI Agent
    Note over agentic_chat: Process each Tool call requested by AI
    agentic_chat ->> agentic_chat: Parse Tool call arguments
    agentic_chat ->> MCP_Client: Call requested Tool with AI-provided arguments
    alt if Tool execution successful
      MCP_Client -->> agentic_chat: Tool result
      agentic_chat ->> AzureAI: Add result to chat context
    else if Tool execution failed
      MCP_Client -->> agentic_chat: Tool error message
      agentic_chat ->> AzureAI: Add error to chat context
    end
    agentic_chat ->> AzureAI: Supply the AI with Tool results
    AzureAI -->> agentic_chat: Updated response with finish reason
  end
  agentic_chat ->> agentic_chat: Extract final response
  agentic_chat -->> Client: Return {response, history}

```
