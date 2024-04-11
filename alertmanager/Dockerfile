FROM prom/alertmanager

COPY alertmanager.yml /alertmanager.yml
COPY templates/ /etc/alertmanager/template/

CMD ["--config.file=/alertmanager.yml"]