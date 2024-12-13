# CITZ IMB AI Example Notebooks

Welcome to the CITZ IMB AI Example Notebooks. This folder contains all the example notebook to get started with AI using BC Laws as an example.

To run the notebooks, you need to have the following prerequisites on your machine:

- S3 access environment variables set (`.docker/.env`)
- VPN access to the BC Gov network
- Docker
- Python 3.8

The best way to run the notebooks is to use the `jupyter-notebook` Docker container.

Use the `compose.controller.yaml` file to start the container. The container will start the Jupyter Notebook server.

In the logs of the container, find the URL for your localhost that includes the authentication token. Use this URL to view the Jupyter Notebook in the browser.

It is also possible to connect to the notebook [using Visual Studio Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks#_connect-to-a-remote-jupyter-server) once the server is running.

The notebooks are organized in a way that you can start from the basics and move to more advanced topics. The notebooks are organized in the following way:

| chapter | Section | Description | Notebook Link |
| --- | --- | --- | --- |
| 1 | Getting Started | This is an example of how to get started with sematic search and RAG using just the act titles | [Example 1](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Introduction/init.ipynb)|
| 2 | Trulens | This is an example of how to use trulens to track the full RAG pipeline | [Example 2]((https://github.com/bcgov/citz-imb-ai/tree/main/examples/Analytics/trulens.ipynb))|
| 3 | Full Law | This is an example of how to get started with sematic search and RAG using the full law text | [Example 3](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Introduction/fullLaw.ipynb)|
| 4 | Neo4j | This is an example of how to get started with neo4j and how to organize all the laws and acts using graph. | [Example 4](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Neo4j/neo4j.ipynb)|
| 5 | Data Cleaning | This is an example of how to store the Acts based on sections and have a chunk size of 256 based on the sentence transformers requirements | [Example 5](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Neo4j/datacleanup_neo4j.ipynb)|
| 6 | KV Caching | This is an example of how to use the key value store to store the embeddings of the acts and use them for the search | [Example 6](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Embeddings/kv_caching.ipynb)|
| 7 | Get Ticket Data | This is an example of how to get the ticket data extracted from an image file using OCR and storing the data in neo4j | [Example 7](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Image%20OCR/get_ticket_dispute.ipynb)|
| 8 | Embedding adaptors | This is an example of how to create and test embedding adaptors based on the feedback collected and stored in Trulens | [Example 8](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Embeddings/embedding_adaptors.ipynb)|
| 9 | Summary Retrieval | This is an example of how to get the summary of the acts based on the search query | [Example 9](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Misc/offenceact_summary_retrieval.ipynb)|
| 10| Glossary | This notebook helps to index all the glossary terms using in BC Laws. [Glossary](https://www.bclaws.gov.bc.ca/glossary.html) | [Example 10](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Embeddings/glossary.ipynb)|
| 11 | Diffgram NER | This notebook helps to connect with diffgram, populate the data, create the task and schema, able to extract the annotated data and trains the NER model using BERT | [Example 11](https://github.com/bcgov/citz-imb-ai/tree/main/examples/NER%20with%20Diffgram/diffgram_postprocessing_NER_training.ipynb)|
| 12 | Pre-annotating data using A.I | This notebook helps to pre-annotate the data using a superior model, feed it back to diiffgram to validate | [Example 12](https://github.com/bcgov/citz-imb-ai/tree/main/examples/NER%20with%20Diffgram/AI_preannotation_full.ipynb)|
| 13 | Community Detection and Relationship Analysis for Glossary Terms Using the Leiden Algorithm | This notebook using the Leiden algorithm to create communities in Neo4j. | [Example 13](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Neo4j/LeidenComunity_glossary.ipynb)|
| 14 | Agentic Legislative Search: BC Laws Knowledge Graph Explorer | An intelligent agent system for querying BC legislative content through a Neo4j knowledge graph, featuring smart query routing (semantic/explicit/graph/community detection), built-in security validations, and structured JSON responses | [Example 14](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Agentic%20Workflow/AI_agentic_workflow.ipynb)|
| 15 | Red Team Testing: BC Laws Knowledge Graph Agent | A systematic red team assessment toolkit for testing the BC Laws Agent, featuring prompt injection testing, Cypher query validation, and JSON response integrity checks. Tests semantic/explicit/graph search routes and validates security measures using Giskard framework | [Example 15](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Agentic%20Workflow/A.I_Agents_RedTeaming_workflow.ipynb) |
| 16 | NER Training with Doccano | This group of notebooks explores the process for annotating using Doccano, training a small model to perform this annotation, and then having that model annotate additional data. | [Example 16](https://github.com/bcgov/citz-imb-ai/tree/main/examples/NER%20Training) |
| 17 | AI-filtered Cipher Query | This example shows how an AI could be used to parse user queries and extract key info on which we filter nodes in Neo4j alongside the vector comparison. | [Example 17](https://github.com/bcgov/citz-imb-ai/tree/main/examples/Filtered%20Cipher%20Query/ai_filtered_cipher.ipynb) |
