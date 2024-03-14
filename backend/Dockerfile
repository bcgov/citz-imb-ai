FROM python:3.12-slim

# Update apt-get
RUN apt-get update -y

# Create and activate venv
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy cached dependencies
COPY .deps .
COPY requirements.txt .

# Install cached dependencies and allow for missing package retrieval
RUN pip install --no-index --find-links=./.deps -r requirements.txt || \
    pip install -r requirements.txt

COPY init.py /app/init.py
COPY init.ipynb /app/init.ipynb
COPY app.py /app/app.py
COPY DB /app/DB

RUN useradd -ms /bin/bash jupyter
EXPOSE 8888
ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]

