from collections import defaultdict
from fastapi import APIRouter, Body, HTTPException
from app.models import neo4j, trulens, rag
from app.models.rag_states import get_state_map, StateType, default_state
from ..common.chat_objects import ChatRequest

router = APIRouter()
kg = None
tru = None


@router.post("/chat/")
async def chat(chat_request: ChatRequest = Body(ChatRequest)):
    chat_history = []
    # Ensure the input is a valid dictionary or object
    if not isinstance(chat_request, ChatRequest):
        raise ValueError("Input should be a valid ChatRequest object")
    # Global variables initialization
    global kg, tru
    rag_fn = rag.get_full_rag()
    if kg is None:
        kg = neo4j.neo4j()
    if tru is None:
        tru = trulens.connect_trulens()

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
            responses = rag_fn.query(
                chat_request.prompt,
                chat_history,
                kg,
                state,
            )
        else:
            # For external sources, like Azure
            responses = []
    record = recording.get()
    return {"responses": responses, "recording": record.record_id}
