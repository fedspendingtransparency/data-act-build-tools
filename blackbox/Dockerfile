FROM prom/blackbox-exporter

RUN mkdir /config
COPY blackbox.yml /config/blackbox.yml
CMD ["--config.file=/config/blackbox.yml --log.level=debug"]
