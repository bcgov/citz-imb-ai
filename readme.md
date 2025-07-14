# CITZ-IMB AI Repository

Welcome to the CITZ-IMB AI repository. This repository contains a collection of tools, workflows, and examples for building, deploying, and maintaining AI models and their infrastructure.

### Introduction

This project aims to provide a comprehensive framework for developing AI solutions, including data preprocessing, model training, deployment, and monitoring. It leverages modern technologies like FastAPI for the backend, various machine learning libraries for model development, and MLOps practices for managing the lifecycle of AI models.

### Getting Started

To get started with the CITZ-IMB AI repository, follow these steps:

### Clone the Repository

```bash
git clone https://github.com/bcgov/citz-imb-ai.git
cd citz-imb-ai
```

### Prerequisite Knowledge

Before diving into this repository, it is beneficial to have a basic understanding of the following concepts and technologies:
- __Python Programming__: Proficiency in Python is essential as the majority of the codebase is written in Python.
- __Machine Learning__: Familiarity with machine learning concepts and libraries such as TensorFlow, PyTorch and libraries like langchain, lamaindex.
- __FastAPI__: Understanding of how to build and deploy APIs using FastAPI.
- __Javascript react__: Understanding of how to build and deploy frontend using react and javascript.
- __Docker__: Experience containerizing applications with Podman or Docker and using Compose for orchestration. 
- __Openshift Kubernetes__: Basic understanding of Openshift/Kubernetes for managing containerized applications.
- __MLOPs (Airflow)__: Familiarity with Apache Airflow or MLOps concepts for workflow orchestration.
- __Graph DB (Neo4j)__: Basic knowledge of graph databases, specifically Neo4j, as it is used in this project.

### Getting started with the project
The best way to get started is to launch the jupyter notebook docker container. The container will start the jupyter notebook server and you can access the notebooks from the browser.

All the example files should be present when you launch the notebook. Try running some of the examples to get started. You may need to install some of the dependencies, connect to the VPN and may need to modify some of the scripts like which folder do you want to download the files to, etc to run the examples.

#### Set Up Local ENV

1. Create and populate a `.docker/.env` file:
   - Check `compose.controller.yaml` to identify necessary environment variables.
   - Obtain values from your team members.
1. Build the Docker images.
1. Open the Jupyter notebook interface at `localhost`.
1. Open a terminal within Jupyter notebook.
1. Run `pip install -r requirements.txt`.
1. Run `dvc pull` to fetch data from S3 (ensure you are connected to the BC Gov VPN). Refer to the detailed instructions in [DVCReadme.md](DVCReadme.md) for setup guidance, troubleshooting, and best practices to avoid common data synchronization issues.&#x20;
1. (Legacy) Run `python s3.py` to download Acts data (ensure you are connected to the BC Gov VPN).
1. Initialize the TruLens database:
   - Create a database named `trulens`.
   - Run the upgrade script located in [trulens\_upgrade.ipynb](examples/Analytics/trulens_upgrade.ipynb) **before** launching the web application.
   - TruLens captures all evaluation data; the web application requires this setup to function correctly.
You are now set to use existing Jupyter notebooks.

**Note**: Always add future dependencies to `requirements.txt` to maintain clarity and prevent code breakage.

For example notebooks, visit: [Examples](https://github.com/bcgov/citz-imb-ai/tree/main/examples)

### Populating Your Neo4j Data

> ⚠️ **Prerequisite**  
This assumes you already have Jupyter Notebook, Airflow, and Neo4j set up.  
If not, please follow the instructions above to spin up all required containers before proceeding.

📄 **Next Step:**  
Refer to [`NEO4J data generation steps`](./documentation/indexing/readme.md) for a detailed breakdown.

---

## Documentation

To navigate all the work done in the project, please refer to the table below:

<table>
    <thead>
        <tr>
            <th colspan="10" align="center">Overview</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td colspan="2" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/documentation/architecture">Architecture</a></td>
            <td colspan="2" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/documentation/detailedflow">Detailed Flow</a></td>
            <td colspan="3" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/documentation/preprocessing">Preprocessing Workflow</a></td>
            <td colspan="3" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/documentation/activelearning">Active Learning Pipeline</a></td>
        </tr>
        <tr>
            <td colspan="10" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/examples">Examples</a></td>
        </tr>
        <tr>
            <th colspan="10">Presentations</th>
        </tr>
        <tr>
            <td colspan="10" align="center"><a href="https://ai-feedback-b875cc-dev.apps.silver.devops.gov.bc.ca/presentation/">Technical Presentation</a></td>
        </tr>
        <tr>
            <th colspan="10"> Web Interface (frontend and backend) </th>
        </tr>
        <tr>
            <td colspan="5" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/web/frontend">Frontend</a></td>
            <td colspan="5" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/web/backend-fastapi">Backend</a></td>
        </tr>
        <tr>
            <th colspan="10"> Feedback infrastructure </th>
        <tr>
        <tr>
            <td colspan="10" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/web/frontend-feedback-analytics"> Embedding Adaptors</a>
        </tr>
        <tr>
            <th colspan="10"> MLOps </th>
        </tr>   
        <tr>
            <td colspan="5" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/mlops"> MLOps</a></td>
            <td colspan="5" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/mlops/orchestration/airflow"> Airflow Scripts</a></td>
        </tr>
        <tr>
            <th colspan="10"> Hardware / HPC </th>
        <tr>
        <tr>
            <td colspan="5 align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/HPC/intelHW"> Intel 3rd Gen Xeon CPU</a>
            </td>
            <td colspan="5" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/HPC/HPC_Embeddings"> HPC  - Embeddings Generation</a>
            </td>
        </tr>
        <tr>
            <th colspan="10">HPC Documentation</th>
        </tr>
        <tr>
            <td colspan="2" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/HPC/HPC_Embeddings/docs/HPC_wordpiece_pretokenizer.md">WordPiece Pre-tokenizer</a></td>
            <td colspan="2" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/HPC/HPC_Embeddings/docs/hashtable_murmur3.md">Murmur3 Hash Table</a></td>
            <td colspan="2" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/HPC/HPC_Embeddings/docs/memory_pool.md">Memory Pool</a></td>
            <td colspan="2" align="center"><a href="github.com/bcgov/citz-imb-ai/tree/main/HPC/HPC_Embeddings/docs/end_to_end_legislative_data_processing.md">End-to-End Legislative Data Processing</a></td>
            </tr    >
    </tbody>
</table>

#### Repository Structure

The repository is organized into several key sections:
    
    - Architecture: Contains the overall architecture and design documents.
    - Preprocessing: Includes data preprocessing workflows and scripts.
    - Examples: Provides example scripts and notebooks to help you get started.
    - Web Interface:
        - Frontend: Source code for the frontend web interface.
        - Backend: FastAPI-based backend service code.
    - Feedback Infrastructure: Components for collecting and analyzing user feedback.
    - MLOps: Tools and scripts for managing the machine learning lifecycle.
    - Hardware: Information and scripts for high-performance computing tasks.

---

By following the links provided in each section, you can navigate to the respective directories and explore the code, documentation, and resources available. This structure is designed to help you quickly find and understand the different components of the project.
