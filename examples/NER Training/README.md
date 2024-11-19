# Name Entity Recognition (NER) Training Process

This README acts as a guide to the files in the NER Training folder.

Users should be able to take existing acts and laws data stored in their local database and use that information to train an AI model for NER tasks.

## Prerequisites

- [Docanno](https://doccano.github.io/doccano/) is installed. This guide uses the Docker Compose version from their guide.
- The [Neo4j](https://neo4j.com/) container is running and populated with data. Connect with team members for how to populate the database.
- Either a local Jupyter server (available in this project's Docker Compose) or access to the AI Operator on OpenShift.
  - The AI Operator will train the model much faster, but connections to AWS Bedrock may be slower. You can use both if you manually upload/download data files between steps.

## General Step Order & Index

1. Export Nodes from Neo4j
1. Convert Nodes
1. Annotate Data
   1. Manually with Doccano
   1. Automatically with AWS Bedrock
1. Train Model
1. Annotation by Model

## Export Nodes from Neo4j

## Convert Nodes

## Annotate Data
### Manually with Doccano

### Automatically with AWS Bedrock

## Train Model

## Annotation by Model
