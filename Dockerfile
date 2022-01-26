FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN apt-get update

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

RUN apt-get install -y nginx

COPY . /app

CMD ["sh", "run.sh"]
