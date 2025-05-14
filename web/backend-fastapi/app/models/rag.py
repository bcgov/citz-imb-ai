from trulens.apps.app import instrument
from app.models import bedrock
import json
from typing import List
from sentence_transformers import CrossEncoder
from ..common.chat_objects import ChatHistory


class get_full_rag:
    @instrument
    def retrieve(self, question: str, kg, state) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return state.query_similar(question, kg)

    @instrument
    def create_prompt(
        self, question: str, context_str: str, chat_history: List[ChatHistory], state
    ) -> str:
        return state.create_prompt(context_str, question, chat_history)

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
        self,
        topk,
        compared_text,
        doc_fields=[{"name": "text", "weight": 1}],
        take_top=5,
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
        return topk.copy()[:take_top]  # Return top k results

    def query_with_history(self, query: str, chat_history: List[ChatHistory]):
        query_with_history = ""
        for chat in chat_history:
            query_with_history = f"{query_with_history} {chat.prompt}"
        query_with_history = f"{query_with_history} {query}"
        return query_with_history

    @instrument
    def query(self, query: str, chat_history: List[ChatHistory], kg, state) -> str:
        query_with_history = self.query_with_history(query, chat_history)
        context_str = self.retrieve(query_with_history, kg, state)
        context_str = self.re_rank_reference(
            context_str,
            query,
        )
        create_prompt = self.create_prompt(query, context_str, chat_history, state)
        bedrock_response = self.get_response(create_prompt, state.kwargs_key)
        pretty_output = self.formatoutput(context_str, bedrock_response)
        return json.dumps(pretty_output)
