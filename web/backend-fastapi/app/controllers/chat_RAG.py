from collections import defaultdict
from fastapi import APIRouter, Body, HTTPException
from app.models import neo4j, trulens, rag
from app.rag_states import ImagesAndChunks, AtomicIndexing, UpdatedChunks, StateType
from ..common.chat_objects import ChatRequest

router = APIRouter()
kg = None
tru = None

# Include active states in this state_list
state_list = [UpdatedChunks, AtomicIndexing, ImagesAndChunks]
state_map = defaultdict()
# Each state must be initialized and added to the state_map
for state in state_list:
    constructed_state = state()
    state_map.update(
        {
            constructed_state.tag: {
                "state": constructed_state,
                "type": constructed_state.type,
                "trulens_id": constructed_state.trulens_id,
                "description": constructed_state.description,
            }
        }
    )


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

    state_entry = state_map.get(chat_request.key)
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
