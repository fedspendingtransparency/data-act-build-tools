FROM nginx:1.23.4

RUN apt update -y && \
    apt install -y curl unzip
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    aws --version

COPY init.sh /init.sh
COPY configs/nginx.conf /etc/nginx/nginx.conf
COPY configs/conf.d/ /etc/nginx/conf.d/

RUN mkdir -p /etc/nginx/ssl/ && \
    chmod +x /init.sh