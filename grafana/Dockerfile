FROM grafana/grafana:10.2.0-ubuntu

ARG NO_PROXY
ARG HTTP_PROXY
ARG HTTPS_PROXY

COPY pca_root_cert.pem /etc/ssl/certs/pca_root_cert.pem

COPY plugins.txt /etc/grafana/
COPY provisioning /etc/grafana/provisioning

RUN while read p; do grafana cli plugins install $p; done < /etc/grafana/plugins.txt

EXPOSE 3000
