FROM prom/alertmanager

COPY alertmanager.yml /alertmanager.yml
COPY templates/ /etc/alertmanager/template/

COPY pca_root_cert.pem /etc/ssl/certs/pca_root_cert.pem

CMD ["--config.file=/alertmanager.yml"]