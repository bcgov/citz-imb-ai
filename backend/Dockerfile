FROM python:3.11-slim

# Set the working directory in the container
RUN apt-get update -y \
    && apt-get install vim -y

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install notebook

EXPOSE 8888

ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]
