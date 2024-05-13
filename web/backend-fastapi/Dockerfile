# 
FROM python:3.11-slim

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --upgrade pip
RUN pip install notebook
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./ /code/

# 
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
#ENTRYPOINT ["jupyter", "notebook","--allow-root","--ip=0.0.0.0","--port=10000","--no-browser"]
CMD ["python", "main.py"]