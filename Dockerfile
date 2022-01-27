FROM python:3.10-slim-buster
LABEL maintainer="penta@skmserver.tk"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx=1.14.2-2+deb10u4 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -d /app -s /bin/bash -G www-data stockstack \
    && mkdir --parents /run/stockstack \
    && chown -R stockstack:www-data /etc/nginx/sites-enabled/ /run/stockstack/

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

USER stockstack


COPY . /app
#COPY run.sh /app/
#COPY stockstacker/ /app/stockstacker/
#COPY stocksheet/ /app/stocksheet/

RUN rm --force /etc/nginx/sites-enabled/default || true \
    && cp ./config/server.conf /etc/nginx/sites-enabled/server.conf

CMD python -m stockstacker
