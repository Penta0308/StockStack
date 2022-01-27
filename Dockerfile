FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx=1.14.2-2+deb10u4 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -d /app -s /bin/bash -G www-data stockstack

RUN chown -R www-data:stockstack

USER stockstack

COPY . /app

COPY run.sh /app/
COPY requirements.txt /app/
COPY stockstacker/ /app/stockstacker/
COPY stocksheet/ /app/stocksheet/

RUN rm --force /etc/nginx/sites-enabled/default || true \
    && mkdir --parents /run/stockstack \
    && cp ./config/server.conf /etc/nginx/sites-enabled/server.conf

CMD ["sh", "run.sh"]
