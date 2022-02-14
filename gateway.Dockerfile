FROM nginx:1.21.6-alpine

COPY ./config/nginx.conf /etc/nginx/nginx.conf
RUN rm --force /etc/nginx/sites-enabled/default || true
COPY ./config/nginx_stockstack.conf /etc/nginx/sites-enabled/nginx_stockstack.conf
