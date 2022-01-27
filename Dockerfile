FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["sh", "run.sh"]
