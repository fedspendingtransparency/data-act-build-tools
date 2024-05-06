FROM prom/blackbox-exporter

RUN mkdir /config
COPY blackbox.yml /config/blackbox.yml

COPY pca_root_cert.pem /etc/ssl/certs/pca_root_cert.pem

CMD ["--config.file=/config/blackbox.yml","--log.level=debug"]
