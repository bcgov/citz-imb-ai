from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from .State import State
from ..models.neo4j import neo4j_vector_search
from ..common.chat_objects import ChatHistory


class UpdatedChunks(State):
    __tag = "v2UpdatedChunks"  # Don't update this
    __version = "1"  # Update this if making changes
    __description = "Updated Chunks"

    __vector_search_query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
        OPTIONAL MATCH (node)-[:REFERENCES]->(refNode)
        RETURN score, node.ActId,  node.RegId as Regulations, node.sectionId, node.sectionName, node.url,  node.text AS text,
        collect({refSectionId: refNode.sectionId, refSectionName: refNode.sectionName, refActId: refNode.ActId, refText: refNode.text}) AS references
        ORDER BY score DESC
    """
    __vector_index = "Acts_Updatedchunks"
    __embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def __init__(self):
        super().__init__(
            self.__tag,
            self.__version,
            index=self.__vector_index,
            query=self.__vector_search_query,
            kwargs_key="mixtral",
            description=self.__description,
        )

    def create_prompt(
        self, context_str, question, chat_history: List[ChatHistory] = []
    ) -> str:
        """
        Generate a response using the given context and chat history.
        """
        chat_history_str = "\n".join(
            [f"Human: {ch.prompt}\nAI: {ch.response}" for ch in chat_history]
        )
        prompt = f"""
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
            {question}

            Provide the most accurate and helpful answer based on the information above. If no answer is found, state that you don't know.
        """
        return prompt

    def query_similar(self, question, kg):
        return neo4j_vector_search(
            kg,
            question,
            self.__embeddings,
            self.__vector_index,
            self.__vector_search_query,
        )
