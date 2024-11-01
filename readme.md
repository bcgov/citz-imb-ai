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
- __Docker__: Knowledge of containerization using Docker.
- __Openshift Kubernetes__: Basic understanding of Openshift/Kubernetes for managing containerized applications.
- __MLOPs (Airflow)__: Familiarity with Apache Airflow or MLOps concepts for workflow orchestration.
- __Graph DB (Neo4j)__: Basic knowledge of graph databases, specifically Neo4j, as it is used in this project.

### Getting started with the project
The best way to get started is to launch the jupyter notebook docker container. The container will start the jupyter notebook server and you can access the notebooks from the browser.

All the example files should be present when you launch the notebook. Try running some of the examples to get started. You may need to install some of the dependencies, connect to the VPN and may need to modify some of the scripts like which folder do you want to download the files to, etc to run the examples.

#### Set Up Local ENV

1. Create and populate a `.docker/.env` file. Identify needed keys based on the listed environment variables for the container in the `compose.controller.yaml` file. Obtain values from team members.
1. Build the docker images.
1. Open Localhost where the jupyter notebook is running.
1. Open terminal on jupyter notebook.
1. Run `pip install -r requirement.txt`.
1. Run python s3.py to download acts. (Make sure you are connected to BC Gov VPN.)

You are now set to use existing jupyter notebooks.

Note: Add future dependences in `requirement.txt` so that we can keep track of the them and avoid code breakage

For all the example notebooks click here: [Examples](https://github.com/bcgov/citz-imb-ai/tree/main/examples)

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
            <td colspan="2" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/architecture">Architecture</a></td>
            <td colspan="2" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/architecture/detailedflow">Detailed Flow</a></td>
            <td colspan="3" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/architecture/preprocessing">Preprocessing Workflow</a></td>
            <td colspan="3" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/architecture/activelearning">Active Learning Pipeline</a></td>
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
            <th colspan="10"> Hardware </th>
        <tr>
        <tr>
            <td colspan="5 align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/HPC/intelHW"> Intel 3rd Gen Xeon CPU</a>
            </td>
            <td colspan="5" align="center"><a href="https://github.com/bcgov/citz-imb-ai/tree/main/HPC/HPC_Embeddings"> HPC  - Embeddings Generation</a>
            </td>
        </tr>
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
