# Gemma 2B Search Classifier Training

This directory contains scripts for fine-tuning a Gemma 2B model to classify legal search queries into different search types (semantic, explicit, global). The trained model helps determine the appropriate search strategy for answering questions about British Columbia laws.

## Purpose

The system classifies questions into three search categories:

- **Semantic**: Questions requiring vector similarity search (e.g., "Do I need to wear a seatbelt in BC?")
- **Explicit**: Questions answerable with Neo4j Cypher queries (e.g., "How many subsections are in this act?")
- **Global**: Questions requiring broader legal domain understanding across multiple documents

## Prerequisites

- Python 3.8 or higher
- At least 16GB RAM (recommended for CPU training)
- Access to Hugging Face Hub (for model downloads) with your own access token
- Neo4j database with BC Laws data (for question generation)
- Azure AI endpoint (for question generation) with environment variables set in your system

## Quick Start

These steps assume that you are currently in the `training_model` directory.

### 1. Environment Setup

Run the setup script to create a virtual environment and install dependencies:

```bash
setup.sh
```

### 2. Generate Training Data

Generate questions from your Neo4j database:

```bash
python generate_questions_from_data.py
```

This script is currently set to generate 5000 examples.
If you'd rather re-use the examples in the initial test of training, find them in our S3 bucket and put them in the `generated_questions` folder.

### 3. Train the Model

Fine-tune the Gemma 2B model:

```bash
python train_gemma_simple.py
```

This task can take a long time. On a system with an M1 processor with 32GB of RAM, it took roughly 41 hours.
You must insert your HuggingFace token in this file before you can download the `gemma-2b` model.

### 4. Test the Trained Model

Use the fine-tuned model for classification:

```bash
python run_gemma_finetuned.py
```

Some sample questions are populated, but you can change them within the file.

## File Descriptions

### `setup.sh`

**Purpose**: Environment setup and dependency installation script.

**What it does**:

- Checks for Python 3 and pip3 availability
- Creates a virtual environment (`venv/`) if it doesn't exist
- Activates the virtual environment
- Installs PyTorch and other dependencies from `requirements_training.txt`
- Provides setup completion confirmation

**Usage**: Run once before starting the training process.

### `generate_questions_from_data.py`

**Purpose**: Generates training data by creating questions from BC Laws stored in Neo4j.

**What it does**:

- Connects to a Neo4j database containing BC Laws data
- Randomly selects documents and sections from the database
- Uses Azure AI to generate relevant questions based on legal content
- Creates categorized questions (semantic, explicit, global)
- Saves questions in JSONL format in the `generated_questions/` directory
- Generates 5,000 questions across multiple files (100 questions per file)

**Requirements**:

- Neo4j database running on `bolt://localhost:7687`
- Azure AI endpoint and API key set as environment variables
- Database populated with BC Laws data using the `v3` label

**Output**: Multiple JSONL files in `generated_questions/` directory, each containing 100 training examples.

### `train_gemma_simple.py`

**Purpose**: Fine-tunes the Gemma 2B model using LoRA (Low-Rank Adaptation) for efficient training.

**What it does**:

- Loads the pre-trained `google/gemma-2b` model from Hugging Face
- Configures the model for CPU-only training (memory efficient)
- Sets up LoRA configuration for parameter-efficient fine-tuning
- Loads training data from `generated_questions/` directory
- Tokenizes and prepares data for causal language modeling
- Trains the model using Hugging Face Trainer
- Saves the fine-tuned model to `./gemma-2b-search-classifier/`

**Key features**:

- CPU-optimized training configuration
- LoRA fine-tuning (only ~0.1% of parameters are trainable)
- Automatic train/validation split (90/10)
- Gradient checkpointing for memory efficiency
- Model testing after training completion

**Output**: Fine-tuned model saved in `./gemma-2b-search-classifier/` directory.

### `run_gemma_finetuned.py`

**Purpose**: Demonstrates how to use the trained model for search type classification.

**What it does**:

- Loads the fine-tuned model from `./gemma-2b-search-classifier/`
- Provides example questions covering different search types
- Generates predictions for each question using the trained model
- Displays the model's classification results
