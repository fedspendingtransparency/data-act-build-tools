
FROM alpine:3.15.0

RUN apk add --no-cache \
        jq \
        python3 \
        py3-pip \
    && pip3 install --upgrade pip \
    && pip3 install --no-cache-dir \
        awscli \
        databricks-cli

