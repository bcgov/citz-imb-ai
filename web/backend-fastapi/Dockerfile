FROM python:3.11-slim

WORKDIR /backend

# Copy requirements definition to container
COPY ./requirements.txt /backend/requirements.txt

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

COPY ./ /backend/

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Make sure the script is executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# 
CMD ["python", "main.py"]
