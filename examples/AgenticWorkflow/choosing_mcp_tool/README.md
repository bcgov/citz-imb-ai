# MCP Agentic Test

This experiment was to test a basic agentic workflow using a set of provided tools.

The tools in this case follow the Model Context Protocol, but they don't run in a separate server.

## Running

To run the test, use `uv`.

1. `uv lock` will install necessary packages.
2. Ensure the ENV variables AZURE_AI_ENDPOINT and AZURE_AI_KEY are set.
3. `uv run main.py` will run the script.
