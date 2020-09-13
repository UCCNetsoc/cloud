FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8 AS dev


FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8 AS prod
RUN apt-get update && apt-get install pigz && apt-get clean
COPY ./v1 /app/v1
COPY requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt

ENV MODULE_NAME=v1.main
ENV VARIABLE_NAME=api

ENTRYPOINT [ "start.sh" "--host", "0.0.0.0", "--port", "8080" ]