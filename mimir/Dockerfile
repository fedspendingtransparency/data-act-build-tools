FROM grafana/mimir:2.10.3

ARG HTTP_PROXY
ARG HTTPS_PROXY

RUN mkdir -p /mimir

RUN chown -R 10001:10001 /mimir

WORKDIR /mimir

COPY pca_root_cert.pem /etc/ssl/certs/pca_root_cert.pem
RUN cat /etc/ssl/certs/pca_root_cert.pem >> /etc/ssl/certs/ca-certificates.crt && \
    chmod a+wrx /etc/ssl/certs/ca-certificates.crt

COPY /config/mimir.yaml /mimir/config.yaml
CMD ["--config.file=/mimir/config.yaml","--validation.max-length-label-value=14000", "-config.expand-env=true"]
