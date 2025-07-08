import requests


class AzureQuery:
    def __init__(self, endpoint, key, token_max=3000):
        self.endpoint = endpoint
        self.key = key
        self.history = []
        self.token_max = token_max

    def call_agent_with_history(self, query, tools=None, role="user"):
        """Supported values for role: 'system', 'assistant', 'user', 'function', 'tool', and 'developer'"""
        self.history.append({"role": role, "content": query})
        headers = {"Content-Type": "application/json", "api-key": self.key}
        body = {
            "messages": self.history,
            "max_tokens": self.token_max,
        }

        # Add tools to the request body if provided
        if tools is not None:
            body["tools"] = tools
            body["tool_choice"] = "auto"  # Let the model choose when to use tools

        response = requests.post(self.endpoint, headers=headers, json=body, timeout=30)

        if response.status_code == 200:
            choice = response.json().get("choices")[0]
            finish_reason = choice.get("finish_reason")
            if finish_reason == "stop":
                text = choice.get("message").get("content", "").strip()
                if text:
                    self.history.append({"role": "assistant", "content": text})
            elif finish_reason == "tool_calls":
                # Add the assistant's message with tool calls to history
                assistant_message = choice.get("message")
                self.history.append(
                    {
                        "role": "assistant",
                        "content": assistant_message.get("content"),
                        "tool_calls": assistant_message.get("tool_calls"),
                    }
                )
            return choice
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def add_tool_response(self, tool_call_id, content):
        """Add a tool response to the conversation history."""
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content)
        self.history.append(
            {"role": "tool", "tool_call_id": tool_call_id, "content": content}
        )

    def append_to_history(self, role, content):
        """Append a message to the conversation history."""
        self.history.append({"role": role, "content": content})

    def add_system_message(self, content):
        """Add a system message to provide context (like database schema)."""
        # System messages should typically be at the beginning
        self.history.insert(0, {"role": "system", "content": content})

    def set_initial_context(self, schema_info):
        """Set database schema information as a system message."""
        schema_message = f"""
        You are an AI assistant that helps users answer questions about BC Laws. 

        This is the database schema information you need to know:
        {schema_info}

        When using the explicit_search tool, generate valid Cypher queries based on this schema.
        When using the semantic_search tool, help users find relevant information using natural language questions.

        Always consider the schema when constructing queries and provide helpful explanations.
        Keep your responses concise and relevant to the user's question.
        """

        self.add_system_message(schema_message)

    def clear_history(self):
        self.history = []


if __name__ == "__main__":
    import os

    # Example usage
    endpoint = os.getenv("AZURE_AI_ENDPOINT")
    key = os.getenv("AZURE_AI_KEY")
    query = "How many Rs in strawberry?"

    # Example MCP tools definition
    example_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state/country, e.g. San Francisco, CA",
                        }
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to calculate",
                        }
                    },
                    "required": ["expression"],
                },
            },
        },
    ]

    azure_query = AzureQuery(endpoint, key)
    print("\nWithout memory:")
    try:
        response = azure_query.call_agent(query, return_raw=True)
        print(response)
        response = azure_query.call_agent("What question did I just ask you?")
        print(response)
    except Exception as e:
        print(e)

    print("\nWith memory:")
    try:
        response = azure_query.call_agent_with_history(query)
        print(response)
        response = azure_query.call_agent_with_history(
            "What question did I just ask you?"
        )
        print(response)
    except Exception as e:
        print(e)

    print("\nWith tools:")
    try:
        response = azure_query.call_agent(
            "What's the weather like in Vancouver, BC?",
            return_raw=True,
            tools=example_tools,
        )
        print(response)
    except Exception as e:
        print(e)
