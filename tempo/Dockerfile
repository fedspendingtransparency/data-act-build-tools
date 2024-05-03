FROM grafana/tempo:2.2.4

COPY ./tempo.yaml /etc/tempo/tempo.yaml

COPY pca_root_cert.pem /etc/ssl/certs/pca_root_cert.pem
RUN cat /etc/ssl/certs/pca_root_cert.pem >> /etc/ssl/certs/ca-certificates.crt && \
    chmod a+wrx /etc/ssl/certs/ca-certificates.crt