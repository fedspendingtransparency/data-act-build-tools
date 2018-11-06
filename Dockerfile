FROM centos:latest

ENV PACKER_VERSION 1.3.2
ENV ANSIBLE_VERSION 2.7.0
ENV TERRAFORM_VERSION 0.11.10

RUN yum update -y && \
    yum install wget -y && \
    yum install unzip -y && \
    yum install https://centos7.iuscommunity.org/ius-release.rpm -y && \
    yum install python36u -y && \
    yum install python36u-pip -y

WORKDIR /root/

# install packer and link to PATH
RUN wget https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip
RUN unzip /root/packer_${PACKER_VERSION}_linux_amd64.zip -d /opt/packer/
RUN ln -s /opt/packer/packer /usr/local/bin/packer

# install ansible
RUN pip3.6 install pip --upgrade
RUN pip3 install ansible==${ANSIBLE_VERSION} virtualenv

# install terraform
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN unzip /root/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /opt/terraform
RUN ln -s /opt/terraform/terraform /usr/local/bin/terraform

# set python path and install pip packages
RUN rm /usr/bin/python && ln -s /usr/bin/python3.6 /usr/bin/python
RUN pip3 install boto3 sh argparse
