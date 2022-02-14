FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN useradd -d /app -s /bin/bash stockstack

COPY stockstack/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

USER stockstack

COPY stockstack/ /app/stockstack/

CMD sh ./stockstack/run.sh
