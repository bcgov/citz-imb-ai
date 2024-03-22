FROM python:3.11-slim

# Set the working directory in the container
RUN apt-get update -y \
    && apt-get install vim -y

WORKDIR /home/jupyter 

COPY . .

RUN pip install --upgrade pip
RUN pip install notebook

RUN useradd -ms /bin/bash jupyter

USER jupyter

ENV PATH="/usr/local/bin:${PATH}"

EXPOSE 8888

ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]
