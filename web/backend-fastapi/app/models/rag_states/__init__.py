# Used to collect all states for export
from .v2_UpdatedChunks import UpdatedChunks
from .v3_AtomicIndexing import AtomicIndexing
from .v4_ImagesAndChunks import ImagesAndChunks
from .State import StateType  # Keep for export purposes

# Include active states in this state_list
active_states = [UpdatedChunks, AtomicIndexing, ImagesAndChunks]

# Assumption that UpdatedChunks will always be present
default_state_class = UpdatedChunks()
default_state = {
    "state": default_state_class,
    "type": default_state_class.type,
    "trulens_id": default_state_class.trulens_id,
    "description": default_state_class.description,
}


def get_state_map():
    state_map = {}
    # Each state must be initialized and added to the state_map
    for state in active_states:
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
    return state_map
