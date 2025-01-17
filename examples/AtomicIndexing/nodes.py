import json


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


def connect_child_to_parent(db, child_id, parent_id):
    edge_query = """
                MATCH (a), (b)
                WHERE elementId(a) = $parent_id AND elementId(b) = $child_id
                CREATE (a)-[r:CONTAINS]->(b)
                RETURN r
              """
    edge_params = {"parent_id": parent_id, "child_id": child_id}
    db.query(edge_query, edge_params)


class Act:
    def __init__(self, act):
        self.title = act.find("act:title").getText()
        self.chapter = act.find("act:chapter").getText()
        self.year = act.find("act:yearenacted").getText()
        self.sections = []
        self.parts = []

        act_content = (
            act.find("act:content") if act.find("act:content") is not None else act
        )
        # Some acts have parts that surround sections!
        act_parts = act_content.find_all("bcl:part", recursive=False)
        for part in act_parts:
            self.addPart(part)

        # For each section, create node
        sections = act_content.find_all("bcl:section", recursive=False)
        for section in sections:
            self.addSection(section)

    def __str__(self):
        return f"""
          #{self.chapter} {self.title} - {self.year}
          {len(self.sections)} sections
        """

    def createQuery(self):
        return """
               CREATE (n:Act {title: $title, year: $year, chapter: $chapter})
               RETURN elementId(n) AS id
               """

    def addNodeToDatabase(self, db, token_splitter, embeddings):
        query = self.createQuery()
        # Parameters for the node
        params = {"title": self.title, "year": self.year, "chapter": self.chapter}

        # Run the query
        result = db.query(query, params=params)

        # Get the ID of the created node
        act_node_id = result[0]["id"] if result else None

        # Add all the child nodes within the act
        for part in self.parts:
            part.addNodeToDatabase(db, act_node_id, token_splitter, embeddings)
        for section in self.sections:
            section.addNodeToDatabase(
                db, act_node_id, token_splitter, embeddings, {"title": section.title}
            )
        return act_node_id

    def addPart(self, part):
        part_node = Part(part)
        self.parts.append(part_node)

    def addSection(self, section):
        section_node = Section(section)
        # Connect section to act
        self.sections.append(section_node)


class Part:
    def __init__(self, part):
        self.title = part.find("bcl:text").getText()
        self.number = part.find("bcl:num").getText()
        self.sections = []
        self.tables = []
        self.conseqheads = []
        self.divisions = []

        # For each section, create node
        sections = part.find_all("bcl:section", recursive=False)
        for section in sections:
            section_node = Section(section)
            # Connect section to part
            self.sections.append(section_node)

        # Add the mix of conseqhead and table blocks
        conseq_and_tables = collect_conseq_and_tables(part)
        for el in conseq_and_tables:
            if el["conseqhead"]:
                self.conseqheads.append(Consequence(el["conseqhead"], el["table"]))
            elif el["table"]:
                self.tables.append(Table(el["table"]))

        # Add divisions
        divisions = part.find_all("bcl:division", recursive=False)
        for division in divisions:
            self.divisions.append(Division(division))

    def createQuery(self):
        return """
               CREATE (n:Part {title: $title, number: $number})
               RETURN elementId(n) AS id
               """

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        query = self.createQuery()
        # Parameters for the node
        params = {"title": self.title, "number": self.number}

        # Run the query
        result = db.query(query, params=params)

        # Get the ID of the created node
        part_id = result[0]["id"] if result else None

        for section in self.sections:
            section.addNodeToDatabase(
                db, part_id, token_splitter, embeddings, {"title": section.title}
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
    def __init__(self, number, text):
        self.number = number
        self.text = text

    def addNodeToDatabase(
        self, db, parent_id, token_splitter, embeddings, unique_params=None
    ):
        query = self.createQuery()

        # Split the text into chunks
        chunks = token_splitter.split_text(self.text)

        previous_node_id = None
        first_node_id = None
        if len(chunks) > 0:
            for i, chunk in enumerate(chunks):
                # Create embedding for the chunk
                text_embedding = embeddings.embed_query(chunk)
                # Parameters for the node
                params = {
                    "number": self.number,
                    "text": chunk,
                    "textEmbedding": text_embedding,
                    "chunk_index": i,
                }

                if unique_params is not None:
                    params.update(unique_params)

                # Run the query
                result = db.query(query, params=params)

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
        else:
            # Create embedding for the node
            text_embedding = embeddings.embed_query(self.text)
            # Parameters for the node
            params = {
                "number": self.number,
                "text": self.text,
                "textEmbedding": text_embedding,
                "chunk_index": 0,
            }

            if unique_params is not None:
                params.update(unique_params)

            # Run the query
            result = db.query(query, params=params)

            # Get the ID of the created node
            node_id = result[0]["id"] if result else None
            first_node_id = node_id

        # Connect the first chunk of these nodes to the parent
        if first_node_id:
            connect_child_to_parent(db, first_node_id, parent_id)

        return first_node_id


class Section(ContentNode):
    def __init__(self, section):
        section_num = (
            section.find("bcl:num", recursive=False).getText()
            if section.find("bcl:num", recursive=False)
            else ""
        )
        section_text = (
            section.find("bcl:text", recursive=False).getText()
            if section.find("bcl:text", recursive=False)
            else ""
        )
        section_title = (
            section.find("bcl:marginalnote", recursive=False).getText()
            if section.find("bcl:marginalnote", recursive=False)
            else ""
        )
        super().__init__(section_num, section_text)
        self.title = section_title
        self.subsections = []
        self.paragraphs = []
        self.definitions = []
        self.tables = []
        self.conseqheads = []

        # Get all subsections
        subsections = section.find_all("bcl:subsection", recursive=False)
        # For each subsection, add to section
        for subsection in subsections:
            subsection_node = Subsection(subsection)
            # Connect subsection to section
            self.subsections.append(subsection_node)
        # Some sections have immediate paragraphs
        paragraphs = section.find_all("bcl:paragraph", recursive=False)
        for paragraph in paragraphs:
            paragraph_node = Paragraph(paragraph)
            # Connect paragraph to section
            self.paragraphs.append(paragraph_node)
        # Add definitions to the section
        definitions = section.find_all("bcl:definition", recursive=False)
        for definition in definitions:
            # Connect definition to section
            definition_node = Definition(definition)
            self.definitions.append(definition_node)
        # Add the mix of conseqhead and table blocks
        conseq_and_tables = collect_conseq_and_tables(section)
        for el in conseq_and_tables:
            if el["conseqhead"]:
                self.conseqheads.append(Consequence(el["conseqhead"], el["table"]))
            elif el["table"]:
                self.tables.append(Table(el["table"]))

    def addNodeToDatabase(
        self, db, parent_id, token_splitter, embeddings, unique_params=None
    ):
        section_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, unique_params
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
        return """
               CREATE (n:Section:Content {title: $title, number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """


class Subsection(ContentNode):
    def __init__(self, subsection):
        # Can't assume these exist for .getText
        subsection_num = (
            subsection.find("bcl:num").getText() if subsection.find("bcl:num") else ""
        )
        subsection_text = (
            subsection.find("bcl:text").getText() if subsection.find("bcl:text") else ""
        )
        super().__init__(subsection_num, subsection_text)
        self.paragraphs = []

        # Get all paragraphs and add to subsection
        paragraphs = subsection.find_all("bcl:paragraph", recursive=False)
        for paragraph in paragraphs:
            paragraph_node = Paragraph(paragraph)
            # Connect paragraph to subsection
            self.paragraphs.append(paragraph_node)

    def createQuery(self):
        return """
               CREATE (n:Subsection:Content {number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """

    def addNodeToDatabase(
        self, db, parent_id, token_splitter, embeddings, unique_params=None
    ):
        subsection_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, unique_params
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
    def __init__(self, paragraph):
        paragraph_num = (
            paragraph.find("bcl:num").getText() if paragraph.find("bcl:num") else ""
        )
        paragraph_text = (
            paragraph.find("bcl:text").getText() if paragraph.find("bcl:text") else ""
        )
        super().__init__(paragraph_num, paragraph_text)
        self.subparagraphs = []

        # Address subparagraphs
        subparagraphs = paragraph.find_all("bcl:subparagraph", recursive=False)
        for subparagraph in subparagraphs:
            subparagraph_node = Subparagraph(subparagraph)
            self.subparagraphs.append(subparagraph_node)

    def createQuery(self):
        return """
               CREATE (n:Paragraph:Content {number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """

    def addNodeToDatabase(
        self, db, parent_id, token_splitter, embeddings, unique_params=None
    ):
        paragraph_id = super().addNodeToDatabase(
            db, parent_id, token_splitter, embeddings, unique_params
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
    def __init__(self, subparagraph):
        subparagraph_num = (
            subparagraph.find("bcl:num").getText()
            if subparagraph.find("bcl:num")
            else ""
        )
        subparagraph_text = (
            subparagraph.find("bcl:text").getText()
            if subparagraph.find("bcl:text")
            else ""
        )
        super().__init__(subparagraph_num, subparagraph_text)

    def createQuery(self):
        return """
               CREATE (n:Subaragraph:Content {number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """


class Definition:
    def __init__(self, definition):
        self.term = None
        self.definition = None

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
            num = paragraph.find("bcl:num").getText()
            text = paragraph.find("bcl:text").getText()
            definition_text += f"\n({num}) {text}"
            subparagraphs = paragraph.find_all("bcl:subparagraph", recursive=False)
            for subparagraph in subparagraphs:
                num = subparagraph.find("bcl:num").getText()
                text = subparagraph.find("bcl:text").getText()
                definition_text += f"\n({num}) {text}"
        # There may be additional text after the paragraphs
        if len(definition_text_blocks) - len(paragraphs) > 1:
            definition_text += (
                "\n" + definition.find_all("bcl:text", recursive=False)[-1].getText()
            )
        self.definition = definition_text

    def createQuery(self):
        return """
               CREATE (n:Definition {term: $term, definition: $definition})
               RETURN elementId(n) AS id
               """

    def addNodeToDatabase(self, db, parent_id):
        # TODO: Should we create embeddings for this?
        query = self.createQuery()
        # Parameters for the node
        params = {"term": self.term, "definition": self.definition}

        # Run the query
        result = db.query(query, params=params)

        # Get the ID of the created node
        node_id = result[0]["id"] if result else None

        if node_id:
            connect_child_to_parent(db, node_id, parent_id)

        return node_id


class Table:
    def __init__(self, table):
        self.rows = []

        # Not all conseqhead tags actually have tables
        if table is None:
            return
        # Identify valid columns and store their headers
        table_header = table.find("oasis:thead")
        table_body = table.find("oasis:tbody")
        rows = table_body.find_all("oasis:trow")
        headers = []
        # Not all tables have the thead tag. Some just use first row of table as header
        if table_header is not None:
            headers = table_header.find_all("oasis:entry")
        else:
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
        return """
            CREATE (n:Table {rows: $rows})
            RETURN elementId(n) AS id
            """

    def addNodeToDatabase(self, db, parent_id):
        # TODO: Should we create embeddings for this? Suggestion: summarize the table and use that summary for embeddings
        query = self.createQuery()
        # Parameters for the node
        params = {
            "rows": json.dumps(self.rows),
        }

        # Run the query
        result = db.query(query, params=params)

        # Get the ID of the created node
        node_id = result[0]["id"] if result else None

        if node_id:
            connect_child_to_parent(db, node_id, parent_id)

        return node_id


class Consequence:
    def __init__(self, conseqhead, table=None):
        self.table = None
        # table = conseqhead.find("oasis:table", recursive=False)
        if table:
            self.table = Table(table)
        self.title = (
            conseqhead.find("bcl:text", recursive=False).getText().strip()
            if conseqhead.find("bcl:text", recursive=False)
            else ""
        )
        self.num = (
            conseqhead.find("bcl:num", recursive=False).getText()
            if conseqhead.find("bcl:num", recursive=False)
            else ""
        )
        self.note = (
            conseqhead.find("bcl:conseqnote", recursive=False).getText().strip()
            if conseqhead.find("bcl:conseqnote", recursive=False)
            else ""
        )

    def createQuery(self):
        return """
            CREATE (n:Consequence {note: $note, number: $number, title: $title})
            RETURN elementId(n) AS id
            """

    def addNodeToDatabase(self, db, parent_id):
        query = self.createQuery()
        # Parameters for the node
        params = {"note": self.note, "number": self.num, "title": self.title}

        # Run the query
        result = db.query(query, params=params)

        # Get the ID of the created node
        node_id = result[0]["id"] if result else None

        if self.table:
            self.table.addNodeToDatabase(db, node_id)

        if node_id:
            connect_child_to_parent(db, node_id, parent_id)

        return node_id


class Division:
    def __init__(self, division):
        self.number = (
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
        # For each section, create node
        sections = division.find_all("bcl:section", recursive=False)
        for section in sections:
            section_node = Section(section)
            # Connect section to part
            self.sections.append(section_node)

    def createQuery(self):
        return """
            CREATE (n:Division {text: $text, number: $number})
            RETURN elementId(n) AS id
            """

    def addNodeToDatabase(self, db, parent_id, token_splitter, embeddings):
        query = self.createQuery()
        # Parameters for the node
        params = {"text": self.text, "number": self.number}

        # Run the query
        result = db.query(query, params=params)

        # Get the ID of the created node
        division_id = result[0]["id"] if result else None

        for section in self.sections:
            section.addNodeToDatabase(
                db, division_id, token_splitter, embeddings, {"title": section.title}
            )
        # Connect the first section node to the act
        if division_id:
            connect_child_to_parent(db, division_id, parent_id)
        return division_id
