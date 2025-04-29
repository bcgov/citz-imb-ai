from neo4j_functions import neo4j
import json


def create_node_key(node_metadata):
    source_document_title = node_metadata.get("document_title")
    source_section_number = node_metadata.get("section_number")
    source_subsection_number = node_metadata.get("subsection_number")
    source_paragraph_number = node_metadata.get("paragraph_number")
    source_subparagraph_number = node_metadata.get("subparagraph_number")
    return ":".join(
        filter(
            lambda x: x is not None,
            [
                source_document_title,
                source_section_number,
                source_subsection_number,
                source_paragraph_number,
                source_subparagraph_number,
            ],
        )
    )


# Gets paged results of content nodes
def get_paged_v3(page=0, size=1000):
    nodes = neo4j.query(
        f"""
          MATCH (n:Content)
          WHERE n:Section OR n:Subsection OR n:Paragraph OR n:Subparagraph
          WITH n
          SKIP {page * size} LIMIT {size}
          RETURN collect(DISTINCT {{ elementId: elementId(n), properties: properties(n), labels: labels(n) }}) AS allNodes
        """
    )
    return nodes[0].get("allNodes")


set = {}
collision_count = 0
collision_map = {}  # Map to store collisions
document_set = {}

# Retrieve nodes from atomic node set
page_number = 0
page_size = 10000
page = get_paged_v3(page_number, 10000)
while len(page) > 0:
    print(page_number)
    for node in page:
        properties = node.get("properties")
        key = create_node_key(properties)
        if set.get(key) is None:
            set[key] = node
        else:
            # print(
            #     page_number,
            #     f"Duplicate key found: {key} for node {node} and {set[key]}",
            # )
            # raise Exception(
            #     f"Duplicate key found: {key} for node {node} and {set[key]}"
            # )
            collision_count += 1
            document_set[properties.get("document_title")] = True
            if key not in collision_map:
                collision_map[key] = [set[key]]  # Add the original node to the list
            collision_map[key].append(node)  # Add the colliding node to the list
    # Move to next page
    page_number += 1
    page = get_paged_v3(page_number, 10000)

print(f"Collision count: {collision_count}")
# print(f"Collision map: {collision_map}")
print(f"Number of keys: {len(collision_map.keys())}")

# Save the collision map to a JSON file
if collision_map:
    with open("collision_map.json", "w") as json_file:
        json.dump(
            collision_map, json_file, indent=4, default=str
        )  # Use default=str to handle non-serializable objects
    print("Collision map saved to 'collision_map.json'")

print(f"Unique Acts/Regulations with collisions: {len(document_set)}")
print(document_set.keys())
