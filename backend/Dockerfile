FROM python:3.11-slim

# Set the working directory in the container
RUN apt-get update -y \
    && apt-get install vim -y

WORKDIR /app

COPY . .


WORKDIR /home/jupyter 

RUN useradd -ms /bin/bash jupyter

USER jupyter

RUN chmod 777 /home/jupyter

RUN pip install --upgrade pip
RUN pip install notebook


# ENV PATH="/usr/local/bin:${PATH}"

ENV PATH="/root/.local/share:${PATH}"

EXPOSE 8888

ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]
