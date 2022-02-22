FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN useradd -d /app -s /bin/bash stockstack

COPY stockstack/requirements.txt /app/stockstack/requirements.txt
RUN pip install --no-cache-dir -r stockstack/requirements.txt

COPY discordbot/requirements.txt /app/discordbot/requirements.txt
RUN pip install --no-cache-dir -r discordbot/requirements.txt

USER stockstack

COPY stockstack/ /app/stockstack/
COPY discordbot/ /app/discordbot/

CMD sh ./discordbot/run.sh
