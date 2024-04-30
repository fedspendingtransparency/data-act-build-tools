FROM grafana/loki

RUN mkdir -p /loki

RUN chown -R 10001:10001 /loki

WORKDIR /loki

COPY ./loki.yaml /loki/config.yaml
COPY pca_root_cert.pem /etc/ssl/certs/pca_root_cert.pem

USER root
RUN cat /etc/ssl/certs/pca_root_cert.pem >> /etc/ssl/certs/ca-certificates.crt && \
    chmod a+wrx /etc/ssl/certs/ca-certificates.crt

USER loki