# Instructions on Indexing and Edge Creation

## Index Data

See file `index_and_insert.py`

This script collects the XML documents of Acts and Regulations from a local directory, breaks them into a series of classes that reflect each part of the legal document (Sections, Paragraphs, etc.), then builds embeddings and inserts them into Neo4j.

1. Update `acts_path` and `regs_path` variables to match where XML files are located.
2. Adjust the chunck size and overlap as needed. Original settings were `chunk_overlap=50, tokens_per_chunk=256`.
3. Update Neo4j parameters for your database.
4. Run script.

## Create Edges Between Atomic Nodes with AI

See file `detect_ref_ai.py`

This is an optional step if you wish to create references between nodes.

This script prompts Amazon Bedrock to extract key information about references to other parts of BC Laws. Once those references are identified, it attempts to create edges between existing nodes created in the Index Data section.

1. Update AWS session keys.
2. Run script.

## Create Edges Between Atomic Nodes with Regex

See file `detect_ref_regex.py`

This file will identify potential references in text of nodes and determine which node it should form the reference edge to. It does not currently handle all types of references, but it can catch a large number of them.
References are created with the name :REFERENCES_v3.

1. Ensure the above steps of Index Data are complete.
2. Run script.

## Test Queries

See file `atomic_simple_query.py`

This file is just for testing queries and seeing the response from Amazon Bedrock. The current version uses the Mixtral model.
This version only queries on the atomic nodes.

1. Update AWS keys and Neo4j parameters.
2. Edit the `question` variable for what you want to ask.
3. Run the script to see the output.

## Connect Atomic Nodes to Updated Chunks

See file `connect_updated_chunks.py`

This script cycles through all known ActIds in the UpdatedChunk nodes.
It then attempts to find a corresponding section in the atomic nodes and creates a relation between them.
It requires `index_and_insert.py` to have been run first.

1. Update Neo4j parameters.
2. Run the script. Corresponding nodes that could not be located will be printed to the console. (Document Name and Section Number)

## Test Connected Queries

See file `connected_simple_query.py`

This file is just for testing queries and seeing the response from Amazon Bedrock. The current version uses the Mixtral model.
This version searches on the UpdatedChunk nodes initially, but pulls additional nodes from the atomic nodes for context.
It only works if you've previously run the `connect_updated_chunks.py` script above.

1. Update AWS keys and Neo4j parameters.
2. Edit the `question` variable for what you want to ask.
3. Run the script to see the output.

## Build Communities

See file `community_generation.ipynb`

This workbook file contains instructions on how to build community clusters using the Leiden algorithm.
Simply follow the queries outlined in the workbook.

## Summarize Communities

See file `community_summarization.py`

This script follows the stages:

- summarizing communities of nodes using AWS Bedrock
- generating embeddings for these summaries
- inserting community nodes into neo4j
- connecting these nodes to other nodes in the same community

Uncomment the function calls at the bottom of the script as needed to only run the parts you require.
