FROM prom/prometheus
ARG token
ARG auth_dir=/etc/prometheus/auth

COPY alerts/ /etc/prometheus/alerts/
RUN mkdir -p ${auth_dir} && \
    echo ${token} > "${auth_dir}/jenkins.txt"
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY alerts/ /etc/prometheus/alerts/

CMD ["--config.file=/etc/prometheus/prometheus.yml", "--web.enable-lifecycle", "--web.enable-admin-api"]