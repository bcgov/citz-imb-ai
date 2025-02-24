# Instructions on Indexing and Edge Creation

## Index Data

See file `index_and_insert.py`

This script collects the XML documents of Acts and Regulations from a local directory, breaks them into a series of classes that reflect each part of the legal document (Sections, Paragraphs, etc.), then builds embeddings and inserts them into Neo4j.

### Steps to Use

1. Update `acts_path` and `regs_path` variables to match where XML files are located.
2. Adjust the chunck size and overlap as needed. Original settings were `chunk_overlap=50, tokens_per_chunk=256`.
3. Update Neo4j parameters for your database.
4. Run script.

## Create Edges

See file `detect_ref_ai.py`

This script prompts Amazon Bedrock to extract key information about references to other parts of BC Laws. Once those references are identified, it attempts to create edges between existing nodes created in the Index Data section.

1. Update AWS session keys.
2. Run script.

## Test Queries

See file `simple_query.py`

This file is just for testing queries and seeing the response from Amazon Bedrock. The current version uses the Mixtral model.

1. Update AWS keys and Neo4j parameters.
2. Edit the `question` variable for what you want to ask.
3. Run the script to see the output.
