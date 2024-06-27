# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the work directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code into the container
COPY . .

# run the application
CMD ["python", "main.py"]
