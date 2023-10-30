FROM grafana/grafana:10.0.0-ubuntu

ARG HTTP_PROXY=http://p1proxy.frb.org:8080 

ARG HTTPS_PROXY=http://p1proxy.frb.org:8080 

COPY --chown=472:472 provisioning /etc/grafana/provisioning
COPY plugins.txt /etc/grafana/

RUN while read p; do grafana-cli plugins install $p; done < /etc/grafana/plugins.txt

EXPOSE 3000

USER root
#RUN apt update
#RUN apk add aws-cli
