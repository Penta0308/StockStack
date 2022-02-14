FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN useradd -d /app -s /bin/bash stockstack

COPY stockstackfe/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

USER stockstack

COPY stockstackfe/ /app/stockstackfe/

CMD sh ./stockstackfe/run.sh
