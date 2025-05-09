from dotenv import load_dotenv
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default argument configuration for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

dag = DAG(
    "atomic_nodes_create_and_join",
    default_args=default_args,
    description="A DAG to create atomic-level nodes from XML files then connect them to UpdatedChunk nodes",
    catchup=False,
    schedule_interval=None,
    tags=["bclaws", "indexing"],
)

# ===============================
# Task 1: Index XML Files
# ===============================
from bs4 import BeautifulSoup, Tag
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from concurrent.futures import ThreadPoolExecutor
from langchain_community.graphs import Neo4jGraph
from pathlib import Path
import os
from threading import current_thread
import traceback
from collections import defaultdict
import json

load_dotenv("/vault/secrets/zuba-secret-dev")

# Set up embeddings and database connection
token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=50, tokens_per_chunk=256
)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

version_tag = "v3"
acts_path = "XML_Acts/"
regs_path = "XML_Regulations/"

NEO4J_URI = "bolt://" + os.getenv("NEO4J_HOST") + ":" + os.getenv("NEO4J_PORT")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DB")

neo4j = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)


# Feature Flags
embed = False


# Included because passing metadata between classes just makes shallow copies
def deep_copy(dict):
    return json.loads(json.dumps(dict))


# Because some tables are surrounded by the conseqhead block and others aren't
# This function handles both cases, returning dicts with both elements
def collect_conseq_and_tables(block):
    # Find all <bcl:conseqhead> and <oasis:table> tags
    elements = block.find_all(["bcl:conseqhead", "oasis:table"])

    # List to store the results
    results = []

    # Iterate through the elements
    for i, element in enumerate(elements):
        if element.name == "conseqhead":
            table_inside = element.find("oasis:table")
            if table_inside:
                # Case: <bcl:conseqhead> contains a table
                results.append({"conseqhead": element, "table": table_inside})
            else:
                # Check if the next element is a table
                next_sibling = element.find_next_sibling()
                if next_sibling and next_sibling.name == "table":
                    results.append({"conseqhead": element, "table": next_sibling})
                else:
                    # Case: <bcl:conseqhead> without a table
                    results.append({"conseqhead": element, "table": None})
        elif element.name == "table":
            # Check if the previous element is a <bcl:conseqhead>
            prev_sibling = element.find_previous_sibling()
            if not (prev_sibling and prev_sibling.name == "conseqhead"):
                # Case: <oasis:table> without a preceding <bcl:conseqhead>
                results.append({"conseqhead": None, "table": element})
    return results


# Add consequences and tables to class
def add_consequence_table(self, el):
    if el["conseqhead"] and el["table"]:
        self.conseqheads.append(
            Consequence(self.version, el["conseqhead"], el["table"], self.metadata)
        )
    elif el["table"]:
        self.tables.append(Table(self.version, el["table"], self.metadata))
    elif el["conseqhead"]:
        self.conseqheads.append(
            Consequence(self.version, el["conseqhead"], None, self.metadata)
        )


# Creates the CONTAINS edge between a child and parent pair
def connect_child_to_parent(db, child_id, parent_id):
    edge_query = f"""
                MATCH (a) WHERE elementId(a) = $parent_id
                MATCH (b) WHERE elementId(b) = $child_id
                CREATE (a)-[r:CONTAINS]->(b)
                RETURN r
              """
    db.query(edge_query, {"parent_id": parent_id, "child_id": child_id})


# Uses string key to determine all tags for a node
def get_node_tags(node_type, version_tag):
    match (node_type):
        case "Act":
            return f":Act:{version_tag}"
        case "Part":
            return f":Part:{version_tag}"
        case "Division":
            return f":Division:{version_tag}"
        case "Section":
            return f":Section:Content:{version_tag}"
        case "Subsection":
            return f":Subsection:Content:{version_tag}"
        case "Paragraph":
            return f":Paragraph:Content:{version_tag}"
        case "Subparagraph":
            return f":Subparagraph:Content:{version_tag}"
        case "Table":
            return f":Table:{version_tag}"
        case "Definition":
            return f":Definition:{version_tag}"
        case "Consequence":
            return f":Consequence:{version_tag}"
        case "Regulation":
            return f":Regulation:{version_tag}"
        case "Schedule":
            return f":Schedule:Content:{version_tag}"
        case _:
            return ""


def get_query_base(node_type, version):
    return f"""
            CREATE (n {get_node_tags(node_type, version)})
            SET n += $params
            RETURN elementId(n) AS id
            """


#####
# Each class below represents an XML element found in the acts and regulations.
# The classes search for expected elements within themselves, construct those classes, then store them in memory.
# Each class comes with its own query and function to add itself to the database.
# Any class that extends the Content class is expected to have text_embeddings.
#####
class Act:
    def __init__(self, version_tag, act):
        self.metadata = defaultdict(lambda: "")
        self.metadata["document_title"] = (
            act.find("act:title").getText() if act.find("act:title") else ""
        )
        self.metadata["act_chapter"] = (
            act.find("act:chapter").getText() if act.find("act:chapter") else ""
        )
        self.metadata["year"] = (
            act.find("act:yearenacted").getText() if act.find("act:yearenacted") else ""
        )
        self.sections = []
        self.parts = []
        self.divisions = []
        self.schedules = []
        self.version = version_tag

        # There may be one content element, many, or none.
        # If none, then use the act body
        act_contents = act.find_all("act:content")
        if len(act_contents) == 0:
            act_contents = [act]

        for act_content in act_contents:
            # Some acts have parts that surround sections!
            act_parts = act_content.find_all("bcl:part", recursive=False)
            for part in act_parts:
                self.parts.append(Part(self.version, part, self.metadata))

            # For each section, create node
            sections = act_content.find_all("bcl:section", recursive=False)
            for section in sections:
                self.sections.append(Section(self.version, section, self.metadata))

            act_divisions = act_content.find_all("bcl:division", recursive=False)
            for division in act_divisions:
                self.divisions.append(Division(self.version, division, self.metadata))

            schedules = act_content.find_all("bcl:schedule", recursive=False)
            for schedule in schedules:
                self.schedules.append(Schedule(self.version, schedule, self.metadata))

    def __str__(self):
        return f"""
          #{self.chapter} {self.title} - {self.year}
          {len(self.sections)} sections
        """

    def createQuery(self):
        return get_query_base("Act", self.version)

    def addNodeToDatabase(self, db, token_splitter, embeddings):
        query = self.createQuery()
        # Parameters for the node
        params = self.metadata

        # Run the query
        wrapped_params = {"params": params}
        result = db.query(query, params=wrapped_params)

        # Get the ID of the created node
        act_node_id = result[0]["id"] if result else None

        # Add all the child nodes within the act
        for part in self.parts:
            part.addNodeToDatabase(db, act_node_id, token_splitter, embeddings)
        for section in self.sections:
            section.addNodeToDatabase(db, act_node_id, token_splitter, embeddings)
        for division in self.divisions:
            division.addNodeToDatabase(db, act_node_id, token_splitter, embeddings)
        for schedule in self.schedules:
            schedule.addNodeToDatabase(db, act_node_id, token_splitter, embeddings)
        return act_node_id


class Part:
    def __init__(self, version_tag, part, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.metadata["part_title"] = (
            part.find("bcl:text").getText() if part.find("bcl:text") else ""
        )
        self.metadata["part_number"] = (
            part.find("bcl:num").getText() if part.find("bcl:num") else ""
        )
        self.sections = []
        self.tables = []
        self.conseqheads = []
        self.divisions = []
        self.version = version_tag

        # For each section, create node
        sections = part.find_all("bcl:section", recursive=False)
        for section in sections:
            section_node = Section(self.version, section, self.metadata)
            # Connect section to part
            self.sections.append(section_node)

        # Add the mix of conseqhead and table blocks
        conseq_and_tables = collect_conseq_and_tables(part)
        for el in conseq_and_tables:
            add_consequence_table(self, el)

        # Add divisions
        divisions = part.find_all("bcl:division", recursive=False)
        for division in divisions:
            self.divisions.append(Division(self.version, division, self.metadata))

    def createQuery(self):
        return get_query_base("Part", self.version)

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        query = self.createQuery()

        # Run the query
        wrapped_params = {"params": self.metadata}
        result = db.query(query, params=wrapped_params)

        # Get the ID of the created node
        part_id = result[0]["id"] if result else None

        for section in self.sections:
            section.addNodeToDatabase(
                db,
                part_id,
                token_splitter,
                embeddings,
            )
        for table in self.tables:
            table.addNodeToDatabase(db, part_id)
        for conseq in self.conseqheads:
            conseq.addNodeToDatabase(db, part_id)
        for div in self.divisions:
            div.addNodeToDatabase(db, part_id, token_splitter, embeddings)
        # Connect the first section node to the act
        if part_id:
            connect_child_to_parent(db, part_id, parent_id)
        return part_id


class ContentNode:
    def __init__(self, text):
        self.text = text

    def addNodeToDatabase(
        self, db, parent_id, token_splitter, embeddings, unique_params=None
    ):
        query = self.createQuery()

        # Split the text into chunks
        chunks = token_splitter.split_text(self.text) if embed else [self.text]

        previous_node_id = None
        first_node_id = None

        for i, chunk in enumerate(chunks):
            # Create embedding for the chunk
            text_embedding = embeddings.embed_query(chunk) if embed else None
            # Parameters for the node
            params = {
                "text": chunk,
                "textEmbedding": text_embedding,
                "chunk_index": i,
            }

            if unique_params is not None:
                params.update(unique_params)

            # Run the query
            wrapped_params = {"params": params}
            result = db.query(query, params=wrapped_params)

            # Get the ID of the created node
            node_id = result[0]["id"] if result else None
            if i == 0:
                first_node_id = node_id

            # If there's a previous chunk, create a relationship to maintain order
            if previous_node_id:
                relationship_query = """
                MATCH (a), (b)
                WHERE elementId(a) = $prev_id AND elementId(b) = $current_id
                CREATE (a)-[r:NEXT]->(b)
                RETURN r
                """
                relationship_params = {
                    "prev_id": previous_node_id,
                    "current_id": node_id,
                }
                db.query(relationship_query, relationship_params)

            previous_node_id = node_id

        # Connect the first chunk of these nodes to the parent
        if first_node_id:
            connect_child_to_parent(db, first_node_id, parent_id)

        return first_node_id


class Section(ContentNode):
    def __init__(self, version_tag, section, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.metadata["section_number"] = (
            section.find("bcl:num", recursive=False).getText()
            if section.find("bcl:num", recursive=False)
            else ""
        )
        section_text = (
            section.find("bcl:text", recursive=False).getText()
            if section.find("bcl:text", recursive=False)
            else ""
        )
        self.metadata["section_title"] = (
            section.find("bcl:marginalnote", recursive=False).getText()
            if section.find("bcl:marginalnote", recursive=False)
            else ""
        )
        super().__init__(section_text)
        self.subsections = []
        self.paragraphs = []
        self.definitions = []
        self.tables = []
        self.conseqheads = []
        self.version = version_tag

        # Get all subsections
        subsections = section.find_all("bcl:subsection", recursive=False)
        # For each subsection, add to section
        for subsection in subsections:
            subsection_node = Subsection(self.version, subsection, self.metadata)
            # Connect subsection to section
            self.subsections.append(subsection_node)
        # Some sections have immediate paragraphs
        paragraphs = section.find_all("bcl:paragraph", recursive=False)
        for paragraph in paragraphs:
            paragraph_node = Paragraph(self.version, paragraph, self.metadata)
            # Connect paragraph to section
            self.paragraphs.append(paragraph_node)
        # Add definitions to the section
        definitions = section.find_all("bcl:definition", recursive=False)
        for definition in definitions:
            # Connect definition to section
            definition_node = Definition(self.version, definition, self.metadata)
            self.definitions.append(definition_node)
        # Add the mix of conseqhead and table blocks
        conseq_and_tables = collect_conseq_and_tables(section)
        for el in conseq_and_tables:
            add_consequence_table(self, el)

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        section_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, self.metadata
        )
        for subsection in self.subsections:
            subsection.addNodeToDatabase(
                db,
                section_id,
                token_splitter,
                embeddings,
            )
        for paragraph in self.paragraphs:
            paragraph.addNodeToDatabase(
                db,
                section_id,
                token_splitter,
                embeddings,
            )
        for definition in self.definitions:
            definition.addNodeToDatabase(db, section_id)
        for table in self.tables:
            table.addNodeToDatabase(db, section_id)
        for conseq in self.conseqheads:
            conseq.addNodeToDatabase(db, section_id)
        return section_id

    def createQuery(self):
        return get_query_base("Section", self.version)


class Subsection(ContentNode):
    def __init__(self, version_tag, subsection, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        # Can't assume these exist for .getText
        self.metadata["subsection_number"] = (
            subsection.find("bcl:num").getText() if subsection.find("bcl:num") else ""
        )
        subsection_text = (
            subsection.find("bcl:text").getText() if subsection.find("bcl:text") else ""
        )
        super().__init__(subsection_text)
        self.paragraphs = []
        self.version = version_tag

        # Get all paragraphs and add to subsection
        paragraphs = subsection.find_all("bcl:paragraph", recursive=False)
        for paragraph in paragraphs:
            paragraph_node = Paragraph(self.version, paragraph, self.metadata)
            # Connect paragraph to subsection
            self.paragraphs.append(paragraph_node)

    def createQuery(self):
        return get_query_base("Subsection", self.version)

    def addNodeToDatabase(
        self,
        db,
        parent_id,
        token_splitter,
        embeddings,
    ):
        subsection_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, self.metadata
        )

        for paragraph in self.paragraphs:
            paragraph_id = paragraph.addNodeToDatabase(
                db,
                subsection_id,
                token_splitter,
                embeddings,
            )
        return subsection_id


class Paragraph(ContentNode):
    def __init__(self, version_tag, paragraph, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.metadata["paragraph_number"] = (
            paragraph.find("bcl:num").getText() if paragraph.find("bcl:num") else ""
        )
        paragraph_text = (
            paragraph.find("bcl:text").getText() if paragraph.find("bcl:text") else ""
        )
        super().__init__(paragraph_text)
        self.subparagraphs = []
        self.version = version_tag

        # Address subparagraphs
        subparagraphs = paragraph.find_all("bcl:subparagraph", recursive=False)
        for subparagraph in subparagraphs:
            subparagraph_node = Subparagraph(self.version, subparagraph, self.metadata)
            self.subparagraphs.append(subparagraph_node)

    def createQuery(self):
        return get_query_base("Paragraph", self.version)

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        paragraph_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, self.metadata
        )
        for subparagraph in self.subparagraphs:
            subparagraph.addNodeToDatabase(
                db,
                paragraph_id,
                token_splitter,
                embeddings,
            )
        return paragraph_id


class Subparagraph(ContentNode):
    def __init__(self, version_tag, subparagraph, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.metadata["subparagraph_number"] = (
            subparagraph.find("bcl:num").getText()
            if subparagraph.find("bcl:num")
            else ""
        )
        subparagraph_text = (
            subparagraph.find("bcl:text").getText()
            if subparagraph.find("bcl:text")
            else ""
        )
        super().__init__(subparagraph_text)
        self.version = version_tag

    def createQuery(self):
        return get_query_base("Subparagraph", self.version)

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        subparagraph_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, self.metadata
        )
        return subparagraph_id


class Definition:
    def __init__(self, version_tag, definition, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.term = None
        self.definition = None
        self.version = version_tag

        # Get the first text block in a definition. This one is guaranteed
        definition_text_blocks = definition.findAll("bcl:text", recursive=False)
        definition_term_block = definition_text_blocks[0].find("in:term")
        # If a term wasn't found, don't bother continuing
        if definition_term_block is None:
            return None
        self.term = definition_term_block.getText()
        definition_text = definition_text_blocks[0].getText()

        # It also may have paragraphs with subparagraphs
        # Extract and format all <bcl:paragraph> elements
        paragraphs = definition.find_all("bcl:paragraph", recursive=False)
        for paragraph in paragraphs:
            num = (
                paragraph.find("bcl:num").getText() if paragraph.find("bcl:num") else ""
            )
            text = (
                paragraph.find("bcl:text").getText()
                if paragraph.find("bcl:text")
                else ""
            )
            definition_text += f"\n({num}) {text}"
            subparagraphs = paragraph.find_all("bcl:subparagraph", recursive=False)
            for subparagraph in subparagraphs:
                num = (
                    subparagraph.find("bcl:num").getText()
                    if subparagraph.find("bcl:num")
                    else ""
                )
                text = (
                    subparagraph.find("bcl:text").getText()
                    if subparagraph.find("bcl:text")
                    else ""
                )
                definition_text += f"\n({num}) {text}"
        # There may be additional text after the paragraphs
        if len(definition_text_blocks) - len(paragraphs) > 1:
            definition_text += (
                "\n" + definition.find_all("bcl:text", recursive=False)[-1].getText()
            )
        self.definition = definition_text

    def createQuery(self):
        return get_query_base("Definition", self.version)

    def addNodeToDatabase(self, db, parent_id):
        query = self.createQuery()
        # Parameters for the node
        params = {
            "term": self.term,
            "definition": self.definition,
        }
        params.update(self.metadata)
        # Run the query
        wrapped_params = {"params": params}
        result = db.query(query, params=wrapped_params)

        # Get the ID of the created node
        node_id = result[0]["id"] if result else None

        if node_id:
            connect_child_to_parent(db, node_id, parent_id)

        return node_id


class Table:
    def __init__(self, version_tag, table, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.rows = []
        self.version = version_tag

        # Not all conseqhead tags actually have tables
        if table is None:
            return
        # Identify valid columns and store their headers
        table_header = table.find("oasis:thead")
        table_body = table.find("oasis:tbody")

        headers = []
        rows = []
        # If no headers or bodies found, the return value is -1. Check for type.
        if isinstance(table_body, Tag):
            rows = table_body.find_all("oasis:trow")
        # Not all tables have the thead tag. Some just use first row of table as header
        if isinstance(table_header, Tag):
            headers = table_header.find_all("oasis:entry")
        elif len(rows) > 1:
            headers = rows[0].find_all("oasis:entry")
            rows = rows[1:]

        column_names = {}
        excluded_columns = set()
        for header in headers:
            column_name = header.getText().strip()
            column_tag = header.get("colname")
            # Some columns are just white space
            if len(column_name) == 0:
                excluded_columns.add(column_tag)
            else:
                # Add columns with Header text to map
                column_names.update({column_tag: column_name})

        # Get all rows in the table
        for i, row in enumerate(rows):
            data = {"row_num": i}
            entries = row.find_all("oasis:entry")
            for entry in entries:
                column_tag = entry.get("colname")
                # Skip columns that are just white space
                if column_tag in excluded_columns:
                    continue
                column_name = column_names.get(column_tag, "unknown")
                data[column_name] = entry.getText().strip()
            self.rows.append(data)

    def createQuery(self):
        return get_query_base("Table", self.version)

    def addNodeToDatabase(self, db, parent_id):
        query = self.createQuery()
        # Parameters for the node
        params = {
            "rows": json.dumps(self.rows),
        }
        params.update(self.metadata)
        # Run the query
        wrapped_params = {"params": params}
        result = db.query(query, params=wrapped_params)

        # Get the ID of the created node
        node_id = result[0]["id"] if result else None

        if node_id:
            connect_child_to_parent(db, node_id, parent_id)

        return node_id


class Consequence:
    def __init__(self, version_tag, conseqhead, table, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.table = table
        self.version = version_tag
        self.metadata["consequence_title"] = (
            conseqhead.find("bcl:text", recursive=False).getText().strip()
            if conseqhead.find("bcl:text", recursive=False)
            else ""
        )
        self.metadata["consequence_number"] = (
            conseqhead.find("bcl:num", recursive=False).getText()
            if conseqhead.find("bcl:num", recursive=False)
            else ""
        )
        self.note = (
            conseqhead.find("bcl:conseqnote", recursive=False).getText().strip()
            if conseqhead.find("bcl:conseqnote", recursive=False)
            else ""
        )
        if table:
            self.table = Table(self.version, table, self.metadata)

    def createQuery(self):
        return get_query_base("Consequence", self.version)

    def addNodeToDatabase(self, db, parent_id):
        query = self.createQuery()
        # Parameters for the node
        params = {
            "note": self.note,
        }
        params.update(self.metadata)
        # Run the query
        wrapped_params = {"params": params}
        result = db.query(query, params=wrapped_params)

        # Get the ID of the created node
        node_id = result[0]["id"] if result else None

        if self.table:
            self.table.addNodeToDatabase(db, node_id)

        if node_id:
            connect_child_to_parent(db, node_id, parent_id)

        return node_id


class Division:
    def __init__(self, version_tag, division, initial_metadata):
        self.metadata = deep_copy(initial_metadata)
        self.metadata["division_number"] = (
            division.find("bcl:num", recursive=False).getText()
            if division.find("bcl:num", recursive=False)
            else ""
        )
        self.text = (
            division.find("bcl:text", recursive=False).getText()
            if division.find("bcl:text", recursive=False)
            else ""
        )
        self.sections = []
        self.version = version_tag
        # For each section, create node
        sections = division.find_all("bcl:section", recursive=False)
        for section in sections:
            section_node = Section(self.version, section, self.metadata)
            # Connect section to part
            self.sections.append(section_node)
        # Some divisions also have parts
        self.parts = []
        parts = division.find_all("bcl:part", recursive=False)
        for part in parts:
            part_node = Part(self.version, part, self.metadata)
            self.parts.append(part_node)

    def createQuery(self):
        return get_query_base("Division", self.version)

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        query = self.createQuery()
        # Parameters for the node
        params = {"text": self.text}
        params.update(self.metadata)
        # Run the query
        wrapped_params = {"params": params}
        result = db.query(query, params=wrapped_params)

        # Get the ID of the created node
        division_id = result[0]["id"] if result else None

        for section in self.sections:
            section.addNodeToDatabase(db, division_id, token_splitter, embeddings)
        for part in self.parts:
            part.addNodeToDatabase(db, division_id, token_splitter, embeddings)
        # Connect the division to its parent
        if division_id:
            connect_child_to_parent(db, division_id, parent_id)
        return division_id


class Regulation:
    def __init__(self, version_tag, regulation):
        self.metadata = defaultdict(lambda: "")
        self.metadata["document_title"] = (
            regulation.find("reg:title").getText()
            if regulation.find("reg:title")
            else ""
        )
        self.metadata["related_act_title"] = (
            regulation.find("reg:acttitle").getText()
            if regulation.find("reg:acttitle")
            else ""
        )
        self.deposit_date = (
            regulation.find("reg:deposited").getText()
            if regulation.find("reg:deposited")
            else ""
        )
        self.sections = []
        self.parts = []
        self.divisions = []
        self.schedules = []
        self.version = version_tag

        # There may be one content element, many, or none.
        # If none, then use the regulation body
        reg_contents = regulation.find_all("reg:content")
        if len(reg_contents) == 0:
            reg_contents = [regulation]

        for reg_content in reg_contents:
            # Some acts have parts that surround sections!
            reg_parts = reg_content.find_all("bcl:part", recursive=False)
            for part in reg_parts:
                self.parts.append(Part(self.version, part, self.metadata))

            # For each section, create node
            sections = reg_content.find_all("bcl:section", recursive=False)
            for section in sections:
                self.sections.append(Section(self.version, section, self.metadata))

            divisions = reg_content.find_all("bcl:division", recursive=False)
            for division in divisions:
                self.divisions.append(Division(self.version, division, self.metadata))

            schedules = reg_content.find_all("bcl:schedule", recursive=False)
            for schedule in schedules:
                self.schedules.append(Schedule(self.version, schedule, self.metadata))

    def createQuery(self):
        return get_query_base("Regulation", self.version)

    def addNodeToDatabase(self, db, token_splitter, embeddings):
        query = self.createQuery()
        # Parameters for the node
        params = {
            "deposit_date": self.deposit_date,
        }
        params.update(self.metadata)
        # Run the query
        wrapped_params = {"params": params}
        result = db.query(query, params=wrapped_params)

        # Get the ID of the created node
        reg_node_id = result[0]["id"] if result else None

        # Add all the child nodes within the regulation
        for part in self.parts:
            part.addNodeToDatabase(db, reg_node_id, token_splitter, embeddings)
        for section in self.sections:
            section.addNodeToDatabase(db, reg_node_id, token_splitter, embeddings)
        for division in self.divisions:
            division.addNodeToDatabase(db, reg_node_id, token_splitter, embeddings)
        for schedule in self.schedules:
            schedule.addNodeToDatabase(db, reg_node_id, token_splitter, embeddings)
        return reg_node_id


class Schedule(ContentNode):
    def __init__(self, version_tag, schedule, initialMetadata):
        self.metadata = deep_copy(initialMetadata)
        self.version = version_tag
        self.conseqheads = []
        self.tables = []
        self.sections = []
        # Text is composed from multiple elements within the Schedule
        text = ""
        misc_text = schedule.find_all(
            name=("bcl:centertext", "bcl:lefttext", "bcl:indent1"), recursive=False
        )
        for e in misc_text:
            text += e.getText()
        super().__init__(text)
        self.title = (
            schedule.find("bcl:scheduletitle").getText()
            if schedule.find("bcl:scheduletitle")
            else ""
        )
        # Add the mix of conseqhead and table blocks
        conseq_and_tables = collect_conseq_and_tables(schedule)
        for el in conseq_and_tables:
            add_consequence_table(self, el)

        # Add any sections
        sections = schedule.find_all("bcl:section", recursive=False)
        for section in sections:
            self.sections.append(Section(self.version, section, self.metadata))

    def createQuery(self):
        return get_query_base("Schedule", self.version)

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        schedule_node_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, self.metadata
        )

        if schedule_node_id:
            connect_child_to_parent(db, schedule_node_id, parent_id)

        # Add all the child nodes within the schedule
        for section in self.sections:
            section.addNodeToDatabase(db, schedule_node_id, token_splitter, embeddings)
        for table in self.tables:
            table.addNodeToDatabase(db, schedule_node_id)
        for conseq in self.conseqheads:
            conseq.addNodeToDatabase(db, schedule_node_id)
        return schedule_node_id


# Function to process and index an act
def process_act(file_name):
    if file_name == "":
        return
    thread = current_thread().name
    print(f"Thread {thread}: {file_name} start")
    with open(f"{acts_path}{file_name}", "r") as f:
        data = f.read()

        act_xml = BeautifulSoup(data, features="xml")
        try:
            ## Part 1 - Break Act into Nodes
            act_node = Act(version_tag, act_xml)

            ## Part 2 - Index Act and Add to Neo4j
            act_id = act_node.addNodeToDatabase(neo4j, token_splitter, embeddings)
            pass
        except Exception as e:
            print(f"Error in {file_name}: {e}")
            print(traceback.format_exc())

    print(f"Thread {thread}: {file_name} end")


# Function to process and index a regulation
def process_regulation(file_name):
    if file_name == "":
        return
    thread = current_thread().name
    print(f"Thread {thread}: {file_name} start")
    with open(f"{regs_path}{file_name}", "r") as f:
        data = f.read()

        reg_xml = BeautifulSoup(data, features="xml")
        try:
            ## Part 1 - Break Regulation into Nodes
            reg_node = Regulation(version_tag, reg_xml)

            ## Part 2 - Index Regulation and Add to Neo4j
            reg_id = reg_node.addNodeToDatabase(neo4j, token_splitter, embeddings)
            pass
        except Exception as e:
            print(f"Error in {file_name}: {e}")
            print(traceback.format_exc())

    print(f"Thread {thread}: {file_name} end")


def index_acts_regs():
    act_directory = Path(acts_path)
    act_file_names = [f.name for f in act_directory.iterdir() if f.is_file()]

    reg_directory = Path(regs_path)
    reg_file_names = [f.name for f in reg_directory.iterdir() if f.is_file()]

    with ThreadPoolExecutor(4) as executor:
        print(f"Using {executor._max_workers} threads")
        list(executor.map(process_act, act_file_names))
        list(executor.map(process_regulation, reg_file_names))


# ===============================
# Task 2: Create IS Edges to UpdatedChunk Nodes
# ===============================


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


def create_is_edges():
    # Get all Act/Reg names
    act_names = neo4j.query(
        """
          MATCH (n:UpdatedChunk)
          RETURN COLLECT(DISTINCT n.ActId) as data
        """
    )
    reg_names = neo4j.query(
        """
          MATCH (n:UpdatedChunk)
          RETURN COLLECT(DISTINCT n.RegId) as data
        """
    )

    with ThreadPoolExecutor(4) as executor:
        print(f"Using {executor._max_workers} threads")
        list(executor.map(connect_updated_chunks, act_names[0].get("data")))
        list(executor.map(connect_updated_chunks, reg_names[0].get("data")))
        print("Done!")


# ===============================
# Task Definitions
# ===============================
index_nodes = PythonOperator(
    task_id="index_atomic_nodes",
    python_callable=index_acts_regs,
    dag=dag,
)

create_is_edges_task = PythonOperator(
    task_id="create_is_edges",
    python_callable=create_is_edges,
    dag=dag,
)

index_nodes >> create_is_edges_task
