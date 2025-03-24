from trulens_eval.tru_custom_app import instrument
from app.models import neo4j, trulens, rag, bedrock
import json
from typing import List
from sentence_transformers import CrossEncoder


def retrieval(query_str, embeddings, kg):
    return neo4j.neo4j_vector_search(query_str, kg)


class ChatHistory:
    def __init__(self, prompt: str, response: str):
        self.prompt = prompt
        self.response = response


class get_top_k:
    @instrument
    def retrieve(self, query: str, kg) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query, kg)

    @instrument
    def query(self, query: str, chat_history: List[ChatHistory], embeddings, kg) -> str:
        context_str = self.retrieve(query, embeddings, kg)
        return context_str


class get_full_rag:
    @instrument
    def retrieve(self, query: str, kg, state) -> list:
        """
        Retrieve relevant text from vector store.
        """
        print("retrieval processing")
        return retrieval(query, kg)

    @instrument
    def create_prompt(
        self, query: str, context_str: str, chat_history: List[ChatHistory]
    ) -> str:
        """
        Generate a response using the given context and chat history.
        """
        chat_history_str = "\n".join(
            [f"Human: {ch.prompt}\nAI: {ch.response}" for ch in chat_history]
        )
        print("chat_history_str: ", chat_history_str)
        messages = f"""
            You are a helpful and knowledgeable assistant. Use the following information to answer the user's question accurately and concisely. Do not provide information that is not supported by the given context or chat history.

            - Use the context and previous chat history to form your answer.
            - Laws and Acts can be used interchangeably.
            - If the answer is not found in the context or chat history, state that you don't know.
            - Do not attempt to fabricate an answer.

            Chat history:
            {chat_history_str}

            Context: 
            {context_str}

            Question: 
            {query}

            Provide the most accurate and helpful answer based on the information above. If no answer is found, state that you don't know.
        """
        return messages

    @instrument
    def get_response(self, prompt, kwargs_key):
        """
        Get a response from Bedrock using the provided prompt.
        """
        return bedrock.get_response(prompt, kwargs_key)

    def formatoutput(self, topk, lm_output):
        prettier = {}
        prettier["llm"] = lm_output
        prettier["topk"] = []
        for k in topk:
            k_obj = {}
            k_obj["score"] = k.get("score", 0)
            if "cross_score" in k:
                k_obj["cross_score"] = k["cross_score"]

            # Add all fields that exist and are not empty
            for field in [
                "ActId",
                "Regulations",
                "sectionId",
                "sectionName",
                "url",
                "file_name",
                "folder",
                "section",
                "subfolder",
                "type",
                "text",
            ]:
                if field in k and k[field]:
                    k_obj[field] = k[field]

            if "references" in k:
                k_obj["references"] = k["references"]

            prettier["topk"].append(k_obj)
        return prettier

    @instrument
    def re_rank_reference(
        self, topk, compared_text, doc_fields=[{"name": "text", "weight": 1}]
    ):
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        for field in doc_fields:
            # Map topk to [compared_text, doc_field] pairs list
            pairs = []
            for doc in topk:
                if field["name"] in doc and doc[field["name"]]:
                    pairs.append([compared_text, doc[field["name"]]])
                else:
                    # Use empty string if field is missing
                    pairs.append([compared_text, ""])

            # Produces list of float values. Higher is more closely related.
            if pairs:
                scores = model.predict(pairs)
                # Apply these scores to the original objects
                for index, _ in enumerate(topk):
                    topk[index]["cross_score"] = (
                        scores[index] * field["weight"]
                    ) + topk[index].get("cross_score", 0)

        # Sort by these new scores
        topk.sort(
            key=lambda x: x.get("cross_score", 0),
            reverse=True,
        )
        return topk

    @instrument
    def query(self, question: str, chat_history: List[ChatHistory], kg, state) -> str:
        context_str = state.query_similar(question, kg)
        prompt = state.create_prompt(context_str, question, chat_history)
        bedrock_response = self.get_response(prompt, state.get_kwargs_key())
        # Rerank to sort references by relevance to response
        context_str = self.re_rank_reference(
            context_str,
            bedrock_response,
            [
                {"name": "text", "weight": 1}
            ],  # Use text field which exists in both schemas
        )

        pretty_output = self.formatoutput(context_str, bedrock_response)
        return json.dumps(pretty_output)
