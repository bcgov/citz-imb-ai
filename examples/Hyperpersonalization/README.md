# Hyperpersonalization Example

This folder contains a demonstration of AI hyperpersonalization using Azure OpenAI and PostgreSQL to create personalized chat experiences that learn from user interactions over time.

## Files Overview

### Core Components

- **`AzureSimple.py`** - A lightweight wrapper class for Azure OpenAI API calls. Handles authentication, request formatting, and response processing for chat completions.

- **`chat_with_ai.py`** - Interactive chat application that connects users to Azure OpenAI while maintaining conversation context in a PostgreSQL database. Stores chat history and generates conversation summaries for future personalization. Important to run this and complete at least one chat before running `user_summary.py`.

- **`user_summary.py`** - Analyzes user chat history to generate personality summaries and update user preferences. Uses AI to extract insights from conversation patterns and updates the user profile accordingly.

### Configuration & Data

- **`sample_preferences.py`** - Defines the structure for user preferences including communication style, interaction dynamics, content preferences, and practical settings. Contains both default values and field definitions for hyperpersonalization.

- **`personalization_tables.sql`** - PostgreSQL database schema defining the `user` and `chat` tables. Stores user profiles, preferences, chat history, and conversation summaries with proper indexing. Run this in your local database before running the other files.

## Setup Requirements

- Azure OpenAI endpoint and API key (set as environment variables)
  - `AZURE_AI_ENDPOINT`
  - `AZURE_AI_KEY`
- PostgreSQL database running locally
  - See the project's `compose.controller.yaml` for a default setup
- Python dependencies from `requirements` file
  - Install with `pip install -r requirements`

This example demonstrates how to build AI systems that learn and adapt to individual users over time, creating more personalized and effective interactions.
