FROM python:3.12-slim

# Set the working directory in the container
RUN apt-get update -y \ 
    && apt-get install vim -y \
    && apt-get install iputils-ping -y\
    && apt-get install net-tools -y  \
    && apt-get install dnsutils -y  

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY init.py /app/init.py
COPY init.ipynb /app/init.ipynb
COPY app.py /app/app.py
COPY DB /app/DB
    
RUN useradd -ms /bin/bash jupyter
EXPOSE 8888                                           
ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]

#RUN python init.py



