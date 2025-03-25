from collections import defaultdict
from fastapi import APIRouter, Body
from app.models import neo4j, trulens, rag
from app.rag_states import v2_UpdatedChunks, v4_ImagesAndChunks, v3_AtomicIndexing
from ..common.chat_objects import ChatRequest

router = APIRouter()
kg = None
tru = None

states = [
    {
        v2_UpdatedChunks.tag: {
            "state": v2_UpdatedChunks.UpdatedChunks(),
            "type": "internal",
            "trulens_id": v2_UpdatedChunks.trulens_id,
            "description": "Updated Chunks",
        },
    },
    {
        v3_AtomicIndexing.tag: {
            "state": v3_AtomicIndexing.AtomicIndexing(),
            "type": "internal",
            "trulens_id": v3_AtomicIndexing.trulens_id,
            "description": "Atomic Indexing",
        }
    },
    {
        v4_ImagesAndChunks.tag: {
            "state": v4_ImagesAndChunks.ImagesAndChunks(),
            "type": "internal",
            "trulens_id": v4_ImagesAndChunks.trulens_id,
            "description": "Images and Chunks",
        }
    },
]
state_map = defaultdict(lambda: states[0])
for state in states:
    state_map.update(state)


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
    tru_rag = trulens.tru_rag(rag_fn, state_entry.get("trulens_id"))

    with tru_rag as recording:
        # Key used to determine class called for query
        if state_entry.get("type") == "internal":
            # For internal operations with Neo4j
            state = state_entry.get("state")
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
