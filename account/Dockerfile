FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./v1 /v1
COPY requirements.txt /v1/requirements.txt

RUN pip3 install -r /v1/requirements.txt

CMD ["uvicorn", "v1.main:v1", "--host", "0.0.0.0", "--port", "8080"]
