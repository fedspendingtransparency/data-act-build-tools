FROM alpine:3.15.0

RUN apk add --no-cache \
        ca-certificates

RUN apk add --no-cache \
        postgresql13 \
        zip \ 
        python3 \
        py3-pip \
    && pip3 install --upgrade pip \
    && pip3 install --no-cache-dir \
        awscli \