import requests


class AzureQuery:
    def __init__(self, endpoint, key, token_max=200):
        self.endpoint = endpoint
        self.key = key
        self.history = []
        self.token_max = token_max

    def call_agent(self, query, return_raw=False):
        headers = {"Content-Type": "application/json", "api-key": self.key}
        body = {
            "messages": [{"role": "user", "content": query}],
            "max_tokens": self.token_max,
        }
        response = requests.post(self.endpoint, headers=headers, json=body)

        if response.status_code == 200:
            if return_raw:
                return response.json()
            else:
                return (
                    response.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def call_agent_with_history(self, query):
        self.history.append({"role": "user", "content": query})
        headers = {"Content-Type": "application/json", "api-key": self.key}
        body = {
            "messages": self.history,
            "max_tokens": self.token_max,
        }
        response = requests.post(self.endpoint, headers=headers, json=body)

        if response.status_code == 200:
            text = (
                response.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if text:
                self.history.append({"role": "system", "content": text})
                return text
            return ""
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def clear_history(self):
        self.history = []


if __name__ == "__main__":
    import os

    # Example usage
    endpoint = os.getenv("AZURE_AI_ENDPOINT")
    key = os.getenv("AZURE_AI_KEY")
    query = "How many Rs in strawberry?"

    azure_query = AzureQuery(endpoint, key)
    print("\nWithout memory:")
    try:
        response = azure_query.call_agent(query)
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
