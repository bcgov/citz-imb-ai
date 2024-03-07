FROM python:3.12-slim

# Set the working directory in the container
RUN apt-get update 
#    && apt-get install vim -y \
#    && apt-get install iputils-ping -y\
#    && apt-get install net-tools -y  \
#    && apt-get install dnsutils -y  

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY init.py /app/init.py
COPY app.py /app/app.py
CMD [ "python3", "-m" , "flask", "run" , "--host=2.2.2.2"]

RUN python init.py



