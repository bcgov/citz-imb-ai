# Neo4j Data Versions

This document outlines the various stages of indexed data that have been added to Neo4j over the life of this project. It should be updated with new information as the data changes or new implementations are added.

Unless otherwise noted, this is an additive approach, keeping the former data versions intact while adding new ones.

## v1 - Chunks

- **Vector Index**: `Acts_chunks`
- **Tokens per Chunk**: `256`
- **Embedding Model**: `all-MiniLM-L6-v2`
- **Embedding Dimensions**: `384`

Text content of Acts and Regulations chunked and inserted as `Chunk` nodes with embeddings.
There is no delineation of this text content apart from the token count.

The only metadata on these nodes apart from the `text` and `textEmbedding` properties are

Examples of graph connections:

- (:Chunk)-\[:PART_OF]->(:Act)-\[:ACT]->(:Law)
- (:Chunk)-\[:PART_OF]->(:Reg)-\[:REGULATIONS]->(:Law)
- (:Chunk)-\[:NEXT]->(:Chunk)

### Node Labels

- Chunk
- Law
- Act
- Reg

### Edge Labels

- NEXT
- PART_OF
- ACT
- REGULATIONS

## v2 - Updated Chunks

- **Vector Index**: `Acts_Updatedchunks`
- **Tokens per Chunk**: `256`
- **Embedding Model**: `all-MiniLM-L6-v2`
- **Embedding Dimensions**: `384`

Text content of Acts and Regulations chunked and inserted as `UpdatedChunk` nodes with embeddings.

In addition to the chunking based on token count, each string of `UpdatedChunk` nodes specifically represent a Section within an Act or Regulation. This Section information is added to the available metadata on each node under the `sectionId` and `sectionName` properties, allowing for a greater ability to specify where the node information originally came from.

In this version Acts and Regulations are differentiated via their metadata. `UpdatedChunk` nodes will have both `ActId` and `RegId` for a Regulation but only `ActId` for Acts.

Examples of graph connections:

- (:UpdatedChunk)-\[:NEXT]->(:UpdatedChunk)

### Node Labels

- UpdatedChunk

### Edge Labels

- NEXT

## v3 - Atomic Indexing

- **Vector Index**: `Acts_Updatedchunks`

No embeddings are created for this version. Initial attempts included embeddings, but the context proved to be too granular to be effective, so a hybrid solution is now used instead.

This version uses the XML version of the Acts and Regulation. It breaks each component found into a unique node with the same label matching its name within the laws. For example, sections are broken into `Section` nodes, paragraphs to `Paragraph` nodes, etc.

Nodes are connected using the `CONTAINS` edge label, indicating that it exists within a parent element within the law.

`Section` nodes are also connected to relative sections from the `UpdatedChunk` nodes via an edge with the `IS` label. When a semantic search is performed on the `UpdatedChunk` nodes, the relevant atomic nodes for that section can now be returned as well, providing a broader context with which an LLM can formulate a response.

These `v3` nodes contain additional metadata about their position within the Acts and Regulations. Properties such as `section_number`, `paragraph_number`, etc. allow for exact references

Examples of graph connections:

- (:UpdatedChunk)-\[:IS]-(:v3:Section)
- (:v3:Section)-\[:CONTAINS]->(:v3:Subsection)

### Node Labels

- v3 -> All atomic nodes have this in addition to a label for their type.
- Act
- Regulation
- Part
- Division
- Section
- Subsection
- Paragraph
- Subparagraph
- Consequence
- Table
- Definition
- Schedule
- Content -> This label was used for nodes that required text embeddings, although it serves no purpose with those embeddings not included.

### Edge Labels

- IS
- CONTAINS

## v4 - Image Indexing

- **Vector Index**: `UpdatedChunksAndImagesv4`
- **Tokens per Chunk**: `256`
- **Embedding Model**: `all-MiniLM-L6-v2`
- **Embedding Dimensions**: `384`
- **OCR Model**: `Claude Sonnet 3.5`

This version adds the ability to include image data when using the vector similarity search.
OCR models are used to summarize the image, and vector embeddings are created for this summarized text.

The nodes that describe images are labelled as `ImageChunk`. They also contain metadata for the original image URL, allowing this image to be found for later presentation.

This version uses a new vector index that includes both the `ImageChunk` and `UpdatedChunk` nodes. This allows for a mix of text and image results to be returned from any query.

Examples of graph connections:

- (:ImageChunk)-\[:NEXT]->(:ImageChunk)
- (:ImageChunk)-\[:PART_OF]->(:Act)

### Node Labels

- ImageChunk
- Act
- Regulation

### Edge Labels

- NEXT
- PART_OF
