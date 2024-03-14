FROM python:3.12-slim

# Set the working directory in the container
RUN apt-get update -y

WORKDIR /app
COPY ./.deps /app/.deps
RUN pip install --no-index --find-links=/app/.deps -r requirements.txt
COPY init.py /app/init.py
COPY init.ipynb /app/init.ipynb
COPY app.py /app/app.py
COPY DB /app/DB

RUN useradd -ms /bin/bash jupyter
EXPOSE 8888
ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=8888","--no-browser"]

#RUN python init.py



