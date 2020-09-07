FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7 AS dev


FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7 AS prod
COPY ./v1 /app/v1
COPY requirements.txt /v1/requirements.txt

RUN pip3 install -r /v1/requirements.txt

ENTRYPOINT [ "start.sh" ]