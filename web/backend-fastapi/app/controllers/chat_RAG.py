from collections import defaultdict
from fastapi import APIRouter, Body
from app.models import neo4j, trulens, rag
from app.rag_states import v2_UpdatedChunks
from ..common.chat_objects import ChatRequest

router = APIRouter()
kg = None
tru = None


state_map = defaultdict()
state_map.update(
    {
        "UpdatedChunks": {
            "state": v2_UpdatedChunks.UpdatedChunks(),
            "type": "internal",
        },
    }
)


# TODO: Define data  model for return value
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
    tru_rag = trulens.tru_rag(rag_fn)

    with tru_rag as recording:
        # Key used to determine class called for query
        state_entry = state_map.get(chat_request.key)
        if state_entry.get("type") == "internal":
            # For internal operations with Neo4j
            responses = rag_fn.query(
                chat_request.prompt,
                chat_history,
                kg,
                state_entry.get("state"),
            )
        else:
            # For external sources, like Azure
            responses = []
    record = recording.get()
    return {"responses": responses, "recording": record.record_id}
