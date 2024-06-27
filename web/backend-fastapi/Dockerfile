FROM python:3.11-slim

# Update the package list and install dos2unix
RUN apt-get update && apt-get install -y dos2unix
RUN apt-get install -y procps
RUN apt-get install -y vim

WORKDIR /backend

# Copy requirements definition to container
COPY ./requirements.txt /backend/requirements.txt

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

# Install gunicorn
RUN pip install gunicorn

COPY ./ /backend/

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Convert the script to Unix-style line endings
RUN dos2unix /usr/local/bin/entrypoint.sh

# Make sure the script is executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# 
#CMD ["python", "main.py"]

# Use Uvicorn to run the FastAPI app with multiple workers
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "8"]

# Use gunicorn to run the FastAPI app with uvicorn workers
CMD ["gunicorn","-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000", "main:app"]