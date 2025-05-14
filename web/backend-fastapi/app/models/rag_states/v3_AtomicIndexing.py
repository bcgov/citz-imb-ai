import json
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from .State import State
from ..neo4j import neo4j_vector_search
from ...common.chat_objects import ChatHistory


class AtomicIndexing(State):
    __tag = "v3AtomicIndexing"  # Don't update this
    __version = "2"  # Update this if making changes
    __description = """
      Structure of data indexing reflects the structure of the Acts and Regulations.
      Uses UpdatedChunks for initial search, then returns all context of matched Sections.
      """

    __vector_search_query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $question) 
        YIELD node, score
        OPTIONAL MATCH (node)-[:IS]-(atomicSection)
        OPTIONAL MATCH (atomicSection)-[:CONTAINS*]->(containedNode)
        OPTIONAL MATCH (containedNode)-[:NEXT*]->(nextNode)
        OPTIONAL MATCH (containedNode)-[:REFERENCES_v3]->(refNode)
        RETURN score, 
              node.ActId AS ActId,  
              node.RegId as Regulations, 
              node.sectionId AS sectionId, 
              node.sectionName AS sectionName, 
              node.url AS url,
              node.type AS type,
              node.text AS text,
            collect(DISTINCT {elementId: elementId(atomicSection), containedProperties: properties(atomicSection)}) + collect(DISTINCT {elementId: elementId(containedNode), containedProperties: properties(containedNode)}) AS atomicNodes,
            collect(DISTINCT {elementId: elementId(refNode), referenceProperties: properties(refNode)}) AS referencedNodes,
            collect(DISTINCT {elementId: elementId(nextNode), nextProperties: properties(nextNode)}) AS nextNodes
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
            top_k=10,
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

        # Only send atomic nodes as context
        # We do not want to send duplicate atomic nodes to the LLM
        # Use this dictionary like a Map of nodes. The key is the elementId.
        context_set = {}
        for record in context_str:
            atomic_nodes = record.get("atomicNodes", [])
            referenced_nodes = record.get("referencedNodes", [])
            next_nodes = record.get("nextNodes", [])
            for list in [atomic_nodes, referenced_nodes, next_nodes]:
                for node in list:
                    node_id = node.get("elementId")
                    if node_id and context_set.get(node_id) is None:
                        context_set[node_id] = node

        # Convert Map back to a list of nodes
        context = context_set.values()

        prompt = f"""
            You are a helpful and knowledgeable assistant. Use the following information to answer the user's question accurately and concisely. Do not provide information that is not supported by the given context or chat history.

            - Use the context to form your answer.
            - Laws and Acts can be used interchangeably.
            - If the answer is not found in the context, state that you don't know.
            - Do not attempt to fabricate an answer.

            Context: 
            {context}

            Question: 
            {question}

            Chat History:
            {chat_history_str}

            Provide the most accurate and helpful answer based on the information above. If no answer is found, state that you don't know.
            In your responses, include references to where this piece of information came from.
            The format should always be (document_title, Section section_number (subsection_number)(paragraph_number)(subparagraph_number))
            Include the reference right after the information it provided.
            If information is from multiple parts of a Section, only reference the Section. For example, if info is from subsection 1, 2, and 3, only reference the Section.
            Not all references will have data for all these fields.
            Include nothing else in the reference.
            If you are not confident about what the reference should be, don't include it.
        """
        return prompt

    def query_similar(self, question, kg):
        return neo4j_vector_search(
            kg,
            question,
            self.__embeddings,
            self.__vector_index,
            self.__vector_search_query,
            self.top_k,
        )
