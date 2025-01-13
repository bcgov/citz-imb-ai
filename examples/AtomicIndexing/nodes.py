class Act:
    def __init__(self, title, chapter, year):
        self.title = title
        self.year = year
        self.chapter = chapter
        self.sections = []
        self.definitions = []

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
        for section in self.sections:
            section_id = section.addNodeToDatabase(
                db, act_node_id, token_splitter, embeddings, {"title": section.title}
            )
            for subsection in section.subsections:
                subsection_id = subsection.addNodeToDatabase(
                    db,
                    section_id,
                    token_splitter,
                    embeddings,
                )
                for paragraph in subsection.paragraphs:
                    paragraph_id = paragraph.addNodeToDatabase(
                        db,
                        subsection_id,
                        token_splitter,
                        embeddings,
                    )
                    for subparagraph in paragraph.subparagraphs:
                        subparagraph.addNodeToDatabase(
                            db,
                            paragraph_id,
                            token_splitter,
                            embeddings,
                        )
            for paragraph in section.paragraphs:
                paragraph_id = paragraph.addNodeToDatabase(
                    db,
                    section_id,
                    token_splitter,
                    embeddings,
                )
                for subparagraph in paragraph.subparagraphs:
                    subparagraph.addNodeToDatabase(
                        db,
                        paragraph_id,
                        token_splitter,
                        embeddings,
                    )
            for definition in section.definitions:
                definition.addNodeToDatabase(db, section_id)
        return act_node_id

    def addSection(self, section):
        section_num = section.find("bcl:num").getText()
        section_text = section.find("bcl:text").getText()
        section_title = section.find("bcl:marginalnote").getText()
        section_node = Section(section_title, section_num, section_text)
        # Get all subsections
        subsections = section.find_all("bcl:subsection", recursive=False)
        # For each subsection, add to section
        for subsection in subsections:
            # Can't assume these exist for .getText
            subsection_num = (
                subsection.find("bcl:num").getText()
                if subsection.find("bcl:num")
                else ""
            )
            subsection_text = (
                subsection.find("bcl:text").getText()
                if subsection.find("bcl:text")
                else ""
            )
            subsection_node = Subsection(subsection_num, subsection_text)
            # Get all paragraphs and add to subsection
            paragraphs = subsection.find_all("bcl:paragraph", recursive=False)
            for paragraph in paragraphs:
                paragraph_num = (
                    paragraph.find("bcl:num").getText()
                    if paragraph.find("bcl:num")
                    else ""
                )
                paragraph_text = (
                    paragraph.find("bcl:text").getText()
                    if paragraph.find("bcl:text")
                    else ""
                )
                paragraph_node = Paragraph(paragraph_num, paragraph_text)
                # Address subparagraphs
                subparagraphs = paragraph.find_all("bcl:subparagraph", recursive=False)
                for subparagraph in subparagraphs:
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
                    subparagraph_node = Subparagraph(
                        subparagraph_num, subparagraph_text
                    )
                    paragraph_node.subparagraphs.append(subparagraph_node)
                # Connect paragraph to subsection
                subsection_node.paragraphs.append(paragraph_node)
            # Connect subsection to section
            section_node.subsections.append(subsection_node)
        # Some sections have immediate paragraphs
        paragraphs = section.find_all("bcl:paragraph", recursive=False)
        for paragraph in paragraphs:
            paragraph_num = (
                paragraph.find("bcl:num").getText() if paragraph.find("bcl:num") else ""
            )
            paragraph_text = (
                paragraph.find("bcl:text").getText()
                if paragraph.find("bcl:text")
                else ""
            )
            paragraph_node = Paragraph(paragraph_num, paragraph_text)
            # Address subparagraphs
            subparagraphs = paragraph.find_all("bcl:subparagraph", recursive=False)
            for subparagraph in subparagraphs:
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
                subparagraph_node = Subparagraph(subparagraph_num, subparagraph_text)
                paragraph_node.subparagraphs.append(subparagraph_node)

            # Connect paragraph to section
            section_node.paragraphs.append(paragraph_node)
        # Add definitions to the section
        definitions = section.find_all("bcl:definition", recursive=False)
        for definition in definitions:
            # Get the first text block in a definition. This one is guaranteed
            definition_text_blocks = definition.findAll("bcl:text", recursive=False)
            definition_term_block = definition_text_blocks[0].find("in:term")
            # If a term wasn't found, don't bother continuing
            if definition_term_block is None:
                return
            definition_term = definition_term_block.getText()
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
                    "\n"
                    + definition.find_all("bcl:text", recursive=False)[-1].getText()
                )
            # Connect definition to section
            definition_node = Definition(definition_term, definition_text)
            section_node.definitions.append(definition_node)
        # Connect section to act
        self.sections.append(section_node)


class ContentNode:
    def __init__(self, number, text, chunkIndex=0):
        self.number = number
        self.text = text
        self.chunk_index = chunkIndex

    def addNodeToDatabase(
        self, db, parent_id, token_splitter, embeddings, unique_params=None
    ):
        query = self.createQuery()

        # Split the text into chunks
        chunks = token_splitter.split_text(self.text)

        previous_node_id = None
        first_node_id = None
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

        # Connect the first section node to the act
        if first_node_id:
            edge_query = """
                MATCH (a), (b)
                WHERE elementId(a) = $parent_id AND elementId(b) = $child_id
                CREATE (a)-[r:CONTAINS]->(b)
                RETURN r
              """
            edge_params = {"parent_id": parent_id, "child_id": first_node_id}
            db.query(edge_query, edge_params)
        return first_node_id


class Section(ContentNode):
    def __init__(self, title, number, text, chunk_index=0):
        super().__init__(number, text, chunk_index)
        self.title = title
        self.subsections = []
        self.paragraphs = []
        self.definitions = []

    def createQuery(self):
        return """
               CREATE (n:Section:Content {title: $title, number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """


class Subsection(ContentNode):
    def __init__(self, number, text, chunk_index=0):
        super().__init__(number, text, chunk_index)
        self.paragraphs = []

    def createQuery(self):
        return """
               CREATE (n:Subsection:Content {number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """


class Paragraph(ContentNode):
    def __init__(self, number, text, chunk_index=0):
        super().__init__(number, text, chunk_index)
        self.subparagraphs = []

    def createQuery(self):
        return """
               CREATE (n:Paragraph:Content {number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """


class Subparagraph(ContentNode):
    def createQuery(self):
        return """
               CREATE (n:Subaragraph:Content {number: $number, text: $text, text_embedding: $textEmbedding, chunk_index: $chunk_index})
               RETURN elementId(n) AS id
               """


class Definition:
    def __init__(self, term, definition):
        self.term = term
        self.definition = definition

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
            edge_query = """
                MATCH (a), (b)
                WHERE elementId(a) = $parent_id AND elementId(b) = $child_id
                CREATE (a)-[r:DEFINED_WITH]->(b)
                RETURN r
              """
            edge_params = {"parent_id": parent_id, "child_id": node_id}
            db.query(edge_query, edge_params)

        return node_id
