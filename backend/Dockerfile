FROM python:3.12-slim

# Set the working directory in the container
RUN apt-get update -y

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

RUN useradd -ms /bin/bash jupyter
EXPOSE 8888
ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]
