# Contains packer/terraform/ansible dependencies in order to run the various *-deploy.py scripts in a container

FROM centos:7

ARG packer_version_arg=1.5.6
ARG ansible_version_arg=2.8.3
ARG terraform_version_arg=0.12.24

ENV PACKER_VERSION=${packer_version_arg}
ENV ANSIBLE_VERSION=${ansible_version_arg}
ENV TERRAFORM_VERSION=${terraform_version_arg}

RUN yum update -y && \
    yum install -y wget && \
    yum install -y unzip && \
    yum install -y https://centos7.iuscommunity.org/ius-release.rpm && \
    yum install -y python36u && \
    yum install -y python36u-pip && \
    yum install -y openssh-clients

WORKDIR /root/workspace
# this variable is used to run packer
ENV USER ec2-user

# install packer and create an symlink on /usr/local
RUN wget https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip
RUN unzip /root/workspace/packer_${PACKER_VERSION}_linux_amd64.zip -d /opt/packer/
RUN ln -s /opt/packer/packer /usr/local/bin/packer

# install ansible
RUN pip3.6 install pip --upgrade
RUN pip3 install ansible==${ANSIBLE_VERSION}

# install terraform and create an symlink on /usr/local
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN unzip /root/workspace/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /opt/terraform
RUN ln -s /opt/terraform/terraform /usr/local/bin/terraform

# install pip packages
RUN pip3 install boto3 sh argparse
