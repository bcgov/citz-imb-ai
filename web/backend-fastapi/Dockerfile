FROM python:3.11-slim

# Change working directory
WORKDIR /backend

COPY ./requirements.txt /backend/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

COPY ./ /backend/

CMD ["python", "main.py"]
