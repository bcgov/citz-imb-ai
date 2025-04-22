import re
from neo4j_functions import neo4j
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
# Retrieve nodes from atomic node set
page_number = 0
page_size = 10000
page = get_paged_v3(page_number, 10000)
while len(page) > 0:
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
    # Move to next page
    page_number += 1
    page = get_paged_v3(page_number, 10000)

print(collision_count)
