FROM grafana/mimir:2.8.0

ARG HTTP_PROXY
ARG HTTPS_PROXY

RUN mkdir -p /mimir

RUN chown -R 10001:10001 /mimir

WORKDIR /mimir

COPY /config/mimir.yaml /mimir/config.yaml
CMD ["--config.file=/mimir/config.yaml","--validation.max-length-label-value=14000"]
