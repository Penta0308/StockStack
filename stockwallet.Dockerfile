FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

COPY stockwallet/requirements.txt /app/stockwallet/requirements.txt
RUN pip install --no-cache-dir -r stockwallet/requirements.txt

USER stockstack

COPY stockwallet/ /app/stockwallet/

CMD python -u -m stockwallet.__main__
