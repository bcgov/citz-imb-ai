from langchain_community.graphs import Neo4jGraph

NEO4J_URI = "bolt://" + "localhost:7687"  # os.getenv("NEO4J_HOST") + ":7687"
NEO4J_USERNAME = "admin"  # os.getenv("NEO4J_USER")
NEO4J_PASSWORD = "admin"  # os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = "neo4j"  # os.getenv('NEO4J_DB')

neo4j = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)

version_tag = "v3"


# Finds a specific node based on node metadata and returns its elementId.
# Based on how metadata is transferred to child nodes,
# specifying only the most specific match is returned.
def find_node(
    document_title,
    section_num=None,
    subsection_num=None,
    paragraph_num=None,
    subparagraph_num=None,
):
    filters = ["n.document_title = $document_title"]
    params = {"document_title": document_title}

    if section_num:
        filters.append("n.section_number = $section_num")
        params["section_num"] = section_num
    if subsection_num:
        filters.append("n.subsection_number = $subsection_num")
        params["subsection_num"] = subsection_num
    if paragraph_num:
        filters.append("n.paragraph_number = $paragraph_num")
        params["paragraph_num"] = paragraph_num
    if subparagraph_num:
        filters.append("n.subparagraph_number = $subparagraph_num")
        params["subparagraph_num"] = subparagraph_num

    where_clause = " AND ".join(filters)

    query = f"""
        MATCH (n:{version_tag})
        WHERE {where_clause}
        RETURN elementId(n) as id
    """

    nodes = neo4j.query(query, params)
    if len(nodes) > 0:
        return nodes[0]["id"]
    return None


# Returns a node specified by its elementId and all of its children.
def get_whole_tree(head_element_id):
    nodes = neo4j.query(
        f"""
        MATCH (a)-[r:CONTAINS|NEXT*]->(b)
        WHERE elementId(a) = "{head_element_id}"
        WITH  collect(DISTINCT {{ elementId: elementId(a), properties: properties(a) }}) + 
              collect(DISTINCT {{ elementId: elementId(b), properties: properties(b) }}) AS allNodes
        RETURN allNodes
        """
    )

    return nodes[0].get("allNodes")


# Returns an existing reference edge between two nodes.
# Will return None if not found
def get_ref_edge(starting_node_id, ending_node_id):
    edge = neo4j.query(
        f"""
        MATCH (a)-[r:REFERENCES]->(b)
        WHERE elementId(a) = "{starting_node_id}" AND elementId(b) = "{ending_node_id}"
        RETURN {{ elementId: elementId(r), weight: r.weight}}           
      """
    )
    return edge


# Updates an existing edge with a new weight value
def update_edge_weight(edge_id, new_weight):
    edge = neo4j.query(
        f"""
          MATCH ()-[r]-() 
          WHERE elementId(r) = "{edge_id}"
          SET r.weight = {new_weight}
          RETURN r
        """
    )
    return edge


# Creates a reference edge between two nodes. Optional weight argument.
def create_reference_edge(starting_node_id, ending_node_id, weight=1):
    edge = neo4j.query(
        f"""
          MATCH (a), (b)
          WHERE elementId(a) = "{starting_node_id}" AND elementId(b) = "{ending_node_id}"
          MERGE (a)-[r:REFERENCES]->(b)
          ON CREATE SET r.weight = {weight}
          RETURN r
        """
    )
    return edge


# Creates an edge (IS) between two nodes to signify they represent the same thing
# Primarily used to connect UpdatedChunk nodes with corresponding atomic nodes
def create_is_edge(node_id_a, node_id_b):
    edge = neo4j.query(
        f"""
          MATCH (a) WHERE elementId(a) = $a
          MATCH (b) WHERE elementId(b) = $b
          MERGE (a)-[r:IS]-(b)
          ON CREATE SET r.weight = 1
          RETURN r
        """,
        {"a": node_id_a, "b": node_id_b},
    )
    return edge


# Gets all UpdatedChunk nodes with a matching ActId property
def get_updated_chunks(act_id):
    nodes = neo4j.query(
        f"""
          MATCH (n:UpdatedChunk) 
          WHERE n.ActId = $act_id
          WITH collect(DISTINCT {{ elementId: elementId(n), properties: properties(n) }}) AS allNodes
          RETURN allNodes
        """,
        {"act_id": act_id},
    )
    return nodes[0].get("allNodes")


# Gets paged results of content nodes
def get_paged_content(page=0, size=1000):
    nodes = neo4j.query(
        f"""
          MATCH (n:Content)
          WITH n
          SKIP {page * size} LIMIT {size}
          RETURN collect(DISTINCT {{ elementId: elementId(n), properties: properties(n) }}) AS allNodes
        """
    )
    return nodes[0].get("allNodes")


### TESTING CASES
# print(find_node("Protection of Public Participation Act"))
# print(find_node("Protection of Public Participation Act", "11"))
# print(find_node("Protection of Public Participation Act", "11", "5"))
# print(find_node("Protection of Public Participation Act", "11", "5", "b"))
# print(find_node("Protection of Public Participation Act", "11", "5", "b", "i"))
