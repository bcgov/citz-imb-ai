# Base stage with common dependencies
FROM python:3.11-slim AS base

# Update the package list and install dos2unix
RUN apt-get update && apt-get install -y dos2unix
RUN apt-get install -y procps
RUN apt-get install -y vim
# To allow for python wheels installs (C extensions)
RUN apt-get install -y python3-dev
RUN apt-get install -y gcc 
# Removes cached package files and deletes package index files
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /backend

# Copy requirements definition to container
COPY ./requirements.txt /backend/requirements.txt

ENV PIP_USE_PEP517=true

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Convert the script to Unix-style line endings
RUN dos2unix /usr/local/bin/entrypoint.sh

# Make sure the script is executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Development stage
FROM base AS dev

# Copy source code (this will be overridden by volume mount in dev)
COPY ./ /backend/

# Use uvicorn with reload for development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--reload"]

# Production stage (default)
FROM base AS prod

# Copy all source code
COPY ./ /backend/

# Use gunicorn to run the FastAPI app with uvicorn workers
CMD ["gunicorn","-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000", "--timeout", "120", "main:app"]
