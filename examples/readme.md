CITZ IMB AI Example Notebooks
=============================   

Welcome to the CITZ IMB AI Example Notebooks. This folder contains all the example notebook to get started with A.I using B.C Laws as an example.

To run the notebooks, you need to have the following installed on your machine:
S3 access + VPN access to the BC Gov network
Docker
Python 3.8

The best way to run the notebooks is to use the docker container. Run the compose.controller.yaml file to start the container. The container will start the jupyter notebook server and you can access the notebooks from the browser.

 The notebooks are organized in a way that you can start from the basics and move to more advanced topics. The notebooks are organized in the following way:


| chapter | Section | Description | Notebook Link |
| --- | --- | --- | --- |
| 1 | Getting Started | This is an example of how to get started with sematic search and RAG using just the act titles | [Example 1](https://github.com/bcgov/citz-imb-ai/tree/main/examples/init.ipynb)
| 2 | Trulens | This is an example of how to use trulens to track the full RAG pipeline | [Example 2]((https://github.com/bcgov/citz-imb-ai/tree/main/examples/trulens.ipynb))
| 3 | Full Law | This is an example of how to get started with sematic search and RAG using the full law text | [Example 3](https://github.com/bcgov/citz-imb-ai/tree/main/examples/fullLaw.ipynb)
| 4 | Neo4j | This is an example of how to get started with neo4j and how to organize all the laws and acts using graph. | [Example 4](https://github.com/bcgov/citz-imb-ai/tree/main/examples/neo4j.ipynb)
| 5 | Data Cleaning | This is an example of how to store the Acts based on sections and have a chunk size of 256 based on the sentence transformers requirements | [Example 5](https://github.com/bcgov/citz-imb-ai/tree/main/examples/datacleanup_neo4j.ipynb)
| 6 | KV Caching | This is an example of how to use the key value store to store the embeddings of the acts and use them for the search | [Example 6](https://github.com/bcgov/citz-imb-ai/tree/main/examples/kv_caching.ipynb)
| 7 | Get Ticket Data | This is an example of how to get the ticket data extracted from an image file using OCR and storing the data in neo4j | [Example 7](https://github.com/bcgov/citz-imb-ai/tree/main/examples/get_ticket_dispute.ipynb)
| 8 | Embedding adaptors | This is an example of how to create and test embedding adaptors based on the feedback collected and stored in Trulens | [Example 8](https://github.com/bcgov/citz-imb-ai/tree/main/examples/embedding_adaptors.ipynb)
| 9 | Summary Retrieval | This is an example of how to get the summary of the acts based on the search query | [Example 9](https://github.com/bcgov/citz-imb-ai/tree/main/examples/offenceact_summary_retrieval.ipynb)
| 10| Glossary | This notebook helps to index all the glossary terms using in BC Laws. [Glossary](https://www.bclaws.gov.bc.ca/glossary.html) | [Example 10](https://github.com/bcgov/citz-imb-ai/tree/main/examples/glossary.ipynb)
| 11 | Diffgram NER | This notebook helps to connect with diffgram, populate the data, create the task and schema, able to extract the annotated data and trains the NER model using BERT | [Example 11](https://github.com/bcgov/citz-imb-ai/tree/main/examples/diffgram_postprocessing_NER_training.ipynb)
| 12 | Pre-annotating data using A.I | This notebook helps to pre-annotate the data using a superior model, feed it back to diiffgram to validate | [Example 12](https://github.com/bcgov/citz-imb-ai/tree/main/examples/AI_preannotation_full.ipynb)
| 13 | Community Detection and Relationship Analysis for Glossary Terms Using the Leiden Algorithm | This notebook helps to pre-annotate the data using a superior model, feed it back to diiffgram to validate | [Example 13](https://github.com/bcgov/citz-imb-ai/tree/main/examples/LeidenComunity_glossary.ipynb)
