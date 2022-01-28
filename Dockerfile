FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx=1.14.2-2+deb10u4 sudo \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY ./config/nginx.conf /etc/nginx/

RUN useradd -d /app -s /bin/bash -G www-data stockstack \
    && mkdir --parents /run/stockstack \
    && chown -R stockstack /etc/nginx/sites-enabled/ /run/stockstack/ /var/log/nginx/

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./config/stockstack_sudoers /app/config/stockstack_sudoers
RUN cat ./config/stockstack_sudoers | (EDITOR="tee -a" visudo)

USER stockstack

COPY . /app
#COPY run.sh /app/
#COPY stockstacker/ /app/stockstacker/
#COPY stocksheet/ /app/stocksheet/

RUN rm --force /etc/nginx/sites-enabled/default || true \
    && cp ./config/nginx_server.conf /etc/nginx/sites-enabled/nginx_server.conf

CMD python -m stockstacker
