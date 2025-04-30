import re
import time
from neo4j_functions import get_paged_content, neo4j
from pathlib import Path
import json
from collections import namedtuple

sample_text = """
Nam sit amet urna lectus section 4. Nam et lacinia ipsum. Mauris.
Aliquam sollicitudin libero section 6.2 sed accumsan pretium.
Maecenas a section 9 (3) turpis eu turpis maximus  aliquet.
Nullam feugiat urna nec dictum laoreet section 3.4 (1)(a).
Section 214.2 nullam ut quam sit amet risus maximus volutpat.
Duis consequat diam commodo urna sagittis mattis section 32 (d).
Section 9 (a)(iv) sed vestibulum enim id turpis vehicula, a rhoncus velit dignissim.
Aliquam a augue at orci viverra auctor section 9 (a) of this act.
Morbi tincidunt nunc vitae section 3 of the Motor Vehicle Act massa vehicula, ac fermentum quam auctor.
Donec nec nunc id ligula facilisis fringilla section 3, 53, and 8.
Aliquam erat volutpat section 2 and 3. Donec nec nunc id ligula facilisis fringilla.
Donec nec nunc id ligula facilisis fringilla section 4 of this appendix.
Donec nec nunc id ligula facilisis fringilla sections 3 and 4 of this Appendix.
Aliquam erat volutpat sections 39, 40 (1) (a) and 40 (2) (a). Donec nec nunc id ligula facilisis fringilla.


Vestibulum malesuada urna subsection (1) fermentum mollis consectetur.
Subsection (3.4)(a) sed a risus eget sem eleifend cursus.
Cras malesuada orci sed arcu subsection (6)(f)(iv) varius viverra quis nec erat.

Fusce in risus nec paragraph (d) dolor commodo accumsan.
Nunc in sem id magna dictum paragraph (a)(iii) auctor.
Paragraph (b)(ii) praesent vehicula purus ut tellus suscipit semper.

Fusce subparagraph (ii) tempor leo dapibus odio blandit scelerisque.
Subparagraph (v) aecenas tempus elit ac bibendum iaculis.
"""

###########################################
# The patterns hidden in the above text are:
# section 4
# section 6.2
# section 9 (3)
# section 3.4 (1)(a)
# Section 214.2
# section 32 (d)
# Section 9 (a)(iv)
# section 9 (a) of this act
# section 3 of the Motor Vehicle Act
# section 3, 53, and 8
# section 2 and 3
# section 4 of this appendix
# sections 3 and 4 of this Appendix
# sections 39, 40 (1) (a) and 40 (2) (a)  <---- Not currently found correctly

# subsection (1)
# Subsection (3.4)(a)
# subsection (6)(f)(iv)

# paragraph (d)
# paragraph (a)(iii)
# Paragraph (b)(ii)

# subparagraph (ii)
# Subparagraph (v)
##########################################

LOGGING = False


def create_node_key(node_metadata):
    """
    Create a unique key for a document node based on its metadata.

    This function generates a string key by joining various document identifiers
    (title, section, subsection, paragraph, and subparagraph numbers) with colons.
    Only non-None values are included in the key.

    Parameters
    ----------
    node_metadata : dict
      A dictionary containing metadata about the document node with potential keys:
      - document_title (str): The title of the document
      - section_number (str): The section number
      - subsection_number (str): The subsection number
      - paragraph_number (str): The paragraph number
      - subparagraph_number (str): The subparagraph number

    Returns
    -------
    str
      A colon-separated string of non-None metadata values that uniquely identifies
      the document node. For example: "Document Title:1:2:3:a"
    """
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


def find_and_standardize_references(text, source_metadata):
    """
    Extract and standardize legal references from text using regular expressions.

    This function identifies references to sections, subsections, paragraphs, and subparagraphs
    in legal text and standardizes them into a consistent format.

    Args:
      text (str): The legal text to search for references.
      source_metadata (dict): Metadata about the source document containing keys like:
        - document_title: Title of the current document
        - act_title: Title of the act (if applicable)
        - section_number: Current section number (for relative references)
        - subsection_number: Current subsection number (for relative references)
        - paragraph_number: Current paragraph letter (for relative references)

    Returns:
      list: A list of dictionaries, each representing a standardized reference with these fields:
        - document_title: The title of the referenced document
        - section_number: The section number (e.g., "1", "2.3")
        - subsection_number: The subsection number (e.g., "1", "2")
        - paragraph_number: The paragraph letter (e.g., "a", "b")
        - subparagraph_number: The subparagraph Roman numeral (e.g., "i", "iv")
        - in_appendix: Boolean indicating if the reference is to an appendix (only for section references)

    Examples:
      >>> metadata = {"document_title": "Example Act", "section_number": "5", "subsection_number": "2"}
      >>> text = "As stated in section 3(1)(a) and subsection (2) of this Act."
      >>> refs = find_and_standardize_references(text, metadata)
      >>> # Will return standardized references to section 3(1)(a) and subsection (2)
    """
    standardized_references = []
    # Finding section references
    # Section pattern that can handle multiple sections (up to 4)
    section_pattern = re.compile(
        r"(?i)(?<!sub)section[s]?\s+"  # Cannot start with sub. Optional s
        r"(\d+(?:\.\d+)?)"  # First section number (e.g., 4, 6.2)
        r"(?:\s*(?:,\s*|,?\s+and\s+|\s+or\s+)(\d+(?:\.\d+)?))?"  # Second section number (optional)
        r"(?:\s*(?:,\s*|,?\s+and\s+|\s+or\s+)(\d+(?:\.\d+)?))?"  # Third section number (optional)
        r"(?:\s*(?:,\s*|,?\s+and\s+|\s+or\s+)(\d+(?:\.\d+)?))?"  # Fourth section number (optional)
        r"(?:\s*\((\d+)\))?"  # Subsection number (e.g., (1))
        r"(?:\s*\(([a-z])\))?"  # Paragraph letter (e.g., (d))
        r"(?:\s*\(([ivxlc]+)\))?"  # Subparagraph Roman numeral (e.g., (iv))
        r"(?:\s+of\s+this\s+(act))?"  # "of this act" (optional)
        r"(?:\s+of\s+the\s+([\w\s]+?\s+Act))?"  # Act name (e.g., "Motor Vehicle Act")
        r"(?:\s+of\s+this\s+(Appendix))?"  # "of this Appendix" (optional)
    )

    # Find all matches
    section_matches = list(section_pattern.finditer(text))

    # Extract and print matches
    if section_matches:
        if LOGGING:
            print("SECTIONS")
        for match in section_matches:
            first_section = match.group(1)
            second_section = match.group(2)
            third_section = match.group(3)
            fourth_section = match.group(4)
            subsection_number = match.group(5)
            paragraph_letter = match.group(6)
            subparagraph_roman = match.group(7)
            act_name = match.group(9)
            from_this_act = bool(match.group(8))
            from_this_appendix = bool(match.group(10))
            if LOGGING:
                print(f"Full Match: {match.group(0)}")
                print(f"Section Number: {first_section}")
                print(f"Second Section Number: {second_section}")
                print(f"Third Section Number: {third_section}")
                print(f"Fourth Section Number: {fourth_section}")
                print(f"Subsection Number: {subsection_number}")
                print(f"Paragraph Letter: {paragraph_letter}")
                print(f"Subparagraph Roman Numeral: {subparagraph_roman}")
                print(f"Act Name: {act_name}")
                print(f"From this act: {from_this_act}")
                print(f"From this Appendix: {from_this_appendix}")
                print("-" * 40)

            # Determine document that this references
            if act_name:
                document_title = act_name
            elif from_this_act and source_metadata.get("act_title"):
                document_title = source_metadata.get("act_title")
            else:
                document_title = source_metadata.get("document_title")

            # Repeat this for all section matches
            for section in filter(
                lambda x: x is not None,
                [
                    first_section,
                    second_section,
                    third_section,
                    fourth_section,
                ],
            ):
                if section:
                    standardized_references.append(
                        {
                            "document_title": document_title,
                            "section_number": section,
                            "subsection_number": subsection_number,
                            "paragraph_number": paragraph_letter,
                            "subparagraph_number": subparagraph_roman,
                            "in_appendix": from_this_appendix,
                        }
                    )

    # Finding subsection references
    subsection_pattern = re.compile(
        r"(?i)subsection\s+\((\d+(?:\.\d+)?)\)"  # Subsection number (e.g., (1))
        r"(?:\s*\(([a-z])\))?"  # Paragraph letter (e.g., (a))
        r"(?:\s*\(([ivxlc]+)\))?"  # Subparagraph Roman numeral (e.g., (iv))
    )

    # Find all matches
    subsection_matches = list(subsection_pattern.finditer(text))

    # Extract and print matches
    if subsection_matches:
        if LOGGING:
            print("SUBSECTIONS")
        for match in subsection_matches:
            if LOGGING:
                print(f"Full Match: {match.group(0)}")
                print(f"Subsection Number: {match.group(1)}")
                print(f"Paragraph Letter: {match.group(2)}")
                print(f"Subparagraph Roman Numeral: {match.group(3)}")
                print("-" * 40)

            standardized_references.append(
                {
                    "document_title": source_metadata.get("document_title"),
                    "section_number": source_metadata.get("section_number"),
                    "subsection_number": match.group(1),
                    "paragraph_number": match.group(2) or None,
                    "subparagraph_number": match.group(3) or None,
                }
            )

    # Finding paragraph references
    paragraph_pattern = re.compile(
        r"(?i)(?<!sub)paragraph\s*\(([a-z])\)"  # Paragraph number (e.g., (d))
        r"(?:\s*\(([ivxlc]+)\))?"  # Subparagraph Roman numeral (e.g., (ii))
    )

    # Find all matches
    paragraph_matches = list(paragraph_pattern.finditer(text))

    # Extract and print matches
    if paragraph_matches:
        if LOGGING:
            print("PARAGRAPHS")
        for match in paragraph_matches:
            if LOGGING:
                print(f"Full Match: {match.group(0)}")
                print(f"Paragraph Letter: {match.group(1)}")
                print(f"Subparagraph Roman Numeral: {match.group(2)}")
                print("-" * 40)
            standardized_references.append(
                {
                    "document_title": source_metadata.get("document_title"),
                    "section_number": source_metadata.get("section_number"),
                    "subsection_number": source_metadata.get("subsection_number"),
                    "paragraph_number": match.group(1),
                    "subparagraph_number": match.group(2) or None,
                }
            )

    # Finding subparagraph references
    subparagraph_pattern = re.compile(
        r"(?i)subparagraph\s*\(([ivxlc]+)\)"  # Subparagraph Roman numeral (e.g., (ii))
    )

    # Find all matches
    subparagraph_matches = list(subparagraph_pattern.finditer(text))
    # Extract and print matches
    if subparagraph_matches:
        if LOGGING:
            print("SUBPARAGRAPHS")
        for match in subparagraph_matches:

            if LOGGING:
                print(f"Full Match: {match.group(0)}")
                print(f"Subparagraph Roman Numeral: {match.group(1)}")
                print("-" * 40)
            standardized_references.append(
                {
                    "document_title": source_metadata.get("document_title"),
                    "section_number": source_metadata.get("section_number"),
                    "subsection_number": source_metadata.get("subsection_number"),
                    "paragraph_number": source_metadata.get("paragraph_number"),
                    "subparagraph_number": match.group(1),
                }
            )

    return standardized_references


# Test sample text here
# find_and_standardize_references(sample_text, {})
# exit()

start_time = time.time()
# Retrieve nodes from atomic node set
page_number = 0
page_size = 10000
page = get_paged_content(page_number, 10000)

# Load node_map from json or build if not found
# This helps with speed on subsequent runs
node_map = {}
atomic_nodes_map_file = Path("./data/community_detection/atomic_nodes_map.json")
if atomic_nodes_map_file.exists():
    print("Loading node_map from json")
    content = atomic_nodes_map_file.read_text()
    node_map = json.loads(content)
else:
    print("Building node_map from neo4j")
    # Build node_map from nodes
    while len(page) > 0:
        for node in page:
            properties = node.get("properties")
            key = create_node_key(properties)
            if node_map.get(key) is None:
                node_map[key] = [node]
            else:
                node_map[key].append(node)
        # Move to next page
        page_number += 1
        page = get_paged_content(page_number, 10000)
    # Save node_map to json
    atomic_nodes_map_file.write_text(json.dumps(node_map, indent=2))


first_match_list = []
shortest_path_list = []
first_match_tuple = namedtuple(
    "first_match_tuple", ["source_element_id", "target_element_id"]
)
shortest_path_tuple = namedtuple(
    "shortest_path_tuple",
    [
        "source_element_id",
        "target_metadata",
    ],
)

print("Finding references")

# For each key in the node map
for key in node_map:
    # Get the nodes for this key
    key_nodes = node_map[key]
    for node in key_nodes:
        source_element_id = node.get("elementId")
        properties = node.get("properties")
        text = properties.get("text")
        if text and len(text) > 0:
            # Build unique node key from its metadata
            source_node_key = create_node_key(properties)
            # Find all matches in the node's text
            references = find_and_standardize_references(
                properties.get("text"),
                {
                    "document_title": properties.get("document_title"),
                    "section_number": properties.get("section_number"),
                    "subsection_number": properties.get("subsection_number"),
                    "paragraph_number": properties.get("paragraph_number"),
                    "subparagraph_number": properties.get("subparagraph_number"),
                    "act_title": properties.get("act_title"),  # Used for regulations
                },
            )
            # Record these references for later
            # Use two lists: one that assumes first appearance is the target, and one that assumes we want the closest matching target
            for ref in references:
                if ref.get("in_appendix"):
                    # Add this to a list with the source id and reference metadata. We will use shortest path to find the target in Neo4j
                    shortest_path_list.append(
                        shortest_path_tuple(source_element_id, ref)
                    )
                else:
                    # Find the best match for this reference in the node map (accept first if multiple matches)
                    key = create_node_key(ref)
                    matches = node_map.get(key)
                    if matches:
                        # Take the first match and get the elementId
                        target_node = matches[0]
                        target_element_id = target_node.get("elementId")
                        first_match_list.append(
                            first_match_tuple(source_element_id, target_element_id)
                        )

print(f"First Match List: {len(first_match_list)}")
print(f"Shortest Past List: {len(shortest_path_list)}")

end_time = time.time()
print(f"Time to find references: {end_time - start_time} seconds")
start_time = time.time()

# Load matches into neo4j
# Convert first_match_list to a list of dictionaries
# Because neo4j doesn't support tuples
rows = [
    {
        "source_element_id": match.source_element_id,
        "target_element_id": match.target_element_id,
    }
    for match in first_match_list
]

# Originally tried to do this via concurrent transactions.
# There's an issue with lock conflicts when the same node is being accessed by multiple transactions
# Changed it to only use a single transaction at a time. Speed is still very good.
# Matches based on the elementId and creates reference edges between two nodes
result = neo4j.query(
    f"""
    UNWIND $rows AS row
    CALL (row) {{
        MATCH (n) WHERE elementId(n) = row.source_element_id
        MATCH (m) WHERE elementId(m) = row.target_element_id
        MERGE (n)-[r:REFERENCES_v3]->(m)
        ON CREATE SET r.weight = 1
        ON MATCH SET r.weight = r.weight + 1
        RETURN row.source_element_id AS source_id, row.target_element_id AS target_id
    }} IN 1 CONCURRENT TRANSACTIONS OF 10000 ROWS
    ON ERROR CONTINUE
    REPORT STATUS AS s
    WITH s WHERE s.errorMessage IS NOT NULL
    RETURN s
    """,
    {"rows": rows},
)
# TODO: There are so few of these cases (<10) that this can wait for now
# Add the shortest path cases as references as well
# Convert shortest_path_list to a list of dictionaries
# Because neo4j doesn't support tuples
# rows = [
#     {
#         "source_element_id": match.source_element_id,
#         "target_metadata": match.target_metadata,
#     }
#     for match in shortest_path_list
# ]
# for row in rows:

# If issues are found, consider running this again and printing them out
print(f"Issues Identified: {len(result)}")
end_time = time.time()
print(f"Time to create edges: {end_time - start_time} seconds")
exit()
