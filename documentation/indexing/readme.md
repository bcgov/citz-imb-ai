## Neo4j Data Generation Steps

> This document provides a step-by-step guide to generate and index the full Neo4j dataset. It assumes Jupyter Notebook, Airflow, and Neo4j are already set up and running. If not, please follow the setup instructions in the main README to launch the necessary containers.

---

### Step 1: Retrieve Source Data from S3

Use the Airflow DAG to download Acts and Regulations data from S3:

```bash
retrieve_data_from_s3_dag
```

This DAG will automatically pull the relevant raw data files to your local environment.

---

### Step 2: Index Acts

Manually run the following notebook to index Acts into Neo4j:

- **Notebook:** `examples/Neo4j/datacleanup_neo4j.ipynb`
- **Status:** No Airflow DAG yet
- **Note:** Execution time varies based on your compute resources.

---

### Step 3: Index Regulations

> ⚠️ **Missing**: This notebook is not yet implemented. A placeholder should be added and flagged for development:

- **Notebook:** `index_regulations.ipynb` *(to be created)*

---

### Step 4: Index Glossary Terms and Relationships

Run the glossary indexing notebook to create nodes and establish `related_Terms` edges:

- **Notebook:** `examples/Embeddings/glossary.ipynb`
- **Planned DAG:** `glossary_dag.py`

---

### Step 5: Index Ticket and Other Image Data

Run the ticket graphics notebook to index visual nodes and relationships:

- **Notebook:** `examples/Image OCR/get_ticket_Dispute.ipynb`
- **Planned DAG:** `ticket_images_dag.py`

---

## Automation Plan: Convert to Airflow DAGs

To ensure reproducibility and automation, the following notebooks will be converted into DAGs:

| Notebook | Planned Airflow DAG |
|----------|---------------------|
| index_acts.ipynb                          | acts_dag.py *(optional)* |
| index_regulations.ipynb                   | regulations_dag.py *(once implemented)* |

---

## Purpose of this Document

This document serves as a reproducibility guide for:
- Regenerating the graph database
- Tracking which notebooks and DAGs were used in production
- Understanding the indexing structure and data flow

All contributors are expected to keep this document updated as new indexing processes or DAGs are added.

