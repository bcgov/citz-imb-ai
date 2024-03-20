FROM python:3.11-slim

# Set the working directory in the container
RUN apt-get update -y \
    && apt-get install vim -y

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY DB /app/DB
COPY ./*.py /app/
COPY ./*.ipynb /app/
RUN pip install -r requirements.txt
#COPY init.py /app/init.py
#COPY init.ipynb /app/init.ipynb
#COPY app.py /app/app.py
#COPY s3.py /app/s3.py
#COPY trulens.py /app/trulens.py

RUN useradd -ms /bin/bash jupyter
EXPOSE 8888 8501                                           
ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]



