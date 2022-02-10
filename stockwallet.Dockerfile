FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

COPY stockwallet/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY stockwallet/ /app/stockwallet/

CMD python -u -m stockwallet.__main__
