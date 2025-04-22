import re
from neo4j_functions import get_paged_content
import csv

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
    standardized_references = []
    # Finding section references
    section_pattern = re.compile(
        r"(?i)(?<!sub)section\s+(\d+(?:\.\d+)?)"  # Section number (e.g., 4, 6.2, 9 (3))
        r"(?:\s*\((\d+)\))?"  # Subsection number (e.g., (1))
        r"(?:\s*\(([a-z])\))?"  # Paragraph letter (e.g., (d))
        r"(?:\s*\(([ivxlc]+)\))?"  # Subparagraph Roman numeral (e.g., (iv))
        r"(?:\s+of\s+this\s+(act))?"  # "of this act" (optional)
        r"(?:\s+of\s+the\s+([\w\s]+?\s+Act))?"  # Act name (e.g., "Motor Vehicle Act")
    )

    # Find all matches
    section_matches = list(section_pattern.finditer(text))

    # Extract and print matches
    if section_matches:
        if LOGGING:
            print("SECTIONS")
        for match in section_matches:
            if LOGGING:
                print(f"Full Match: {match.group(0)}")
                print(f"Section Number: {match.group(1)}")
                print(f"Subsection Number: {match.group(2)}")
                print(f"Paragraph Letter: {match.group(3)}")
                print(f"Subparagraph Roman Numeral: {match.group(4)}")
                print(f"Act Name: {match.group(6)}")
                print(f"From this act: {bool(match.group(5))}")
                print("-" * 40)

            # Determine document that this references
            if match.group(6):
                document_title = match.group(6)
            elif bool(match.group(5)) and source_metadata.get("act_title"):
                document_title = source_metadata.get("act_title")
            else:
                document_title = source_metadata.get("document_title")
            standardized_references.append(
                {
                    "document_title": document_title,
                    "section_number": match.group(1),
                    "subsection_number": match.group(2) or None,
                    "paragraph_number": match.group(3) or None,
                    "subparagraph_number": match.group(4) or None,
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


# Retrieve nodes from atomic node set
page_number = 0
page_size = 10000
page = get_paged_content(page_number, 10000)
while len(page) > 0:
    with open(
        f"./data/reference_csv/relationships_{str(page_number).zfill(4)}.csv", "w"
    ) as f:
        print("Processing page", page_number)
        write = csv.writer(f)
        headers = ["source_node_key", "target_node_key"]
        write.writerow(headers)
        write = csv.writer(f)
        relationships = []
        # For each node, look for referneces
        for node in page:
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
                        "act_title": properties.get(
                            "act_title"
                        ),  # Used for regulations
                    },
                )
                # Add node keys to list of relationships
                for ref in references:
                    target_node_key = create_node_key(ref)
                    relationships.append((source_node_key, target_node_key))
                    if LOGGING:
                        print(f"{source_node_key} -> {target_node_key}")

        # Write relationships to CSV
        write.writerows(relationships)

    # Move to next page
    page_number += 1
    page = get_paged_content(page_number, 10000)
