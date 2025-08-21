from collections import defaultdict
from fastapi import HTTPException
from app.shared.models import neo4j, trulens, rag
from app.shared.models.rag_states import (
    get_state_map,
    StateType,
    default_state,
    get_states_for_frontend,
)
from ..models.chat_model import ChatRequest, ChatResponse, StateResponse


class ChatService:
    def __init__(self):
        self.kg = None
        self.tru = None
    
    def _initialize_components(self):
        """Initialize knowledge graph and trulens if not already done"""
        if self.kg is None:
            self.kg = neo4j.neo4j()
        if self.tru is None:
            self.tru = trulens.connect_trulens()
    
    async def process_chat(self, chat_request: ChatRequest) -> ChatResponse:
        """Process chat request and return response"""
        chat_history = []
        
        # Ensure the input is a valid ChatRequest object
        if not isinstance(chat_request, ChatRequest):
            raise ValueError("Input should be a valid ChatRequest object")
        
        # Initialize components
        self._initialize_components()
        rag_fn = rag.get_full_rag()
        
        # Determine which state to use
        state_map = get_state_map()
        state_entry = state_map.get(chat_request.key, default_state)
        if state_entry is None:
            raise HTTPException(status_code=404, detail="RAG state not found")
        
        state = state_entry.get("state")
        tru_rag = trulens.tru_rag(rag_fn, state.trulens_id)
        
        with tru_rag as recording:
            # Key used to determine class called for query
            if state.type == StateType.INTERNAL:
                # For internal operations with Neo4j
                response = rag_fn.query(
                    chat_request.prompt,
                    chat_history,
                    self.kg,
                    state,
                )
                responses = [response]
            else:
                # For external sources, like Azure
                responses = []
        
        record = recording.get()
        return ChatResponse(responses=responses, recording=record.record_id)
    
    async def get_available_states(self) -> StateResponse:
        """Get available RAG states for frontend"""
        states = get_states_for_frontend()
        return StateResponse(states=states)
