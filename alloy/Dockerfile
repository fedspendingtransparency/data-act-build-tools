FROM grafana/alloy

ARG token
ARG auth_dir=/etc/alloy/auth

RUN apt update -y && \
    apt-get -y install curl unzip jq

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

RUN mkdir -p ${auth_dir} && \
    echo ${token} > "${auth_dir}/jenkins.txt"    
RUN mkdir -p /etc/alloy
WORKDIR /etc/alloy

COPY ./config/ /etc/alloy/
COPY entry_script.sh /entry_script.sh
COPY pca_root_cert.pem /etc/ssl/certs/pca_root_cert.pem
RUN cat /etc/ssl/certs/pca_root_cert.pem >> /etc/ssl/certs/ca-certificates.crt && \
    chmod a+wrx /etc/ssl/certs/ca-certificates.crt
    
EXPOSE 4317
EXPOSE 4318

ENTRYPOINT [ "/bin/bash" ]
CMD [ "/entry_script.sh" ]