FROM grafana/loki

RUN mkdir -p /loki

RUN chown -R 10001:10001 /loki

WORKDIR /loki

COPY ./loki.yaml /loki/config.yaml
RUN mkdir -p /loki/etc/loki/ssl/

EXPOSE 3100