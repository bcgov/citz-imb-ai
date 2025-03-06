# Creates IS edges between all UpdatedChunk nodes and their relevant atomic node
from concurrent.futures import ThreadPoolExecutor

from neo4j_functions import (
    find_node,
    create_is_edge,
    get_updated_chunks,
)


def connect_updated_chunks(act_id):
    # Get all desired chunks
    chunks = get_updated_chunks(act_id)

    for chunk in chunks:
        # Extract useful properties
        chunk_id = chunk.get("elementId")
        properties = chunk.get("properties")
        chunk_document = properties.get("RegId") or properties.get("ActId")
        chunk_section = properties.get("sectionId")
        # Find an atomic node that matches the act and section
        atomic_node_id = find_node(chunk_document, chunk_section)
        if atomic_node_id:
            edge = create_is_edge(chunk_id, atomic_node_id)
            # If no edge was created, don't proceed with the internal reference edges
            if not edge:
                print(":IS edge not created", chunk.get("elementId"), atomic_node_id)
                continue

        else:
            print(
                "No atomic node found",
                chunk.get("elementId"),
                chunk_document,
                chunk_section,
            )


act_names = ["Motor Vehicle Act"]
with ThreadPoolExecutor() as executor:
    print(f"Using {executor._max_workers} threads")
    list(executor.map(connect_updated_chunks, act_names))
    print("Done!")
