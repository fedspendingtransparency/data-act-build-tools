# Contains packer/terraform/ansible dependencies in order to run the various *-deploy.py scripts in a container

FROM centos:7

ARG packer_version_arg=1.6.1
ARG ansible_version_arg=2.9.15
ARG terraform_version_arg=0.12.31
ARG terragrunt_version_arg=0.25.4
ARG ami_manager_arg=0.8.0
ARG node_version_arg=12.x
ARG pip_install_version=21.1.3

ENV PACKER_VERSION=${packer_version_arg}
ENV ANSIBLE_VERSION=${ansible_version_arg}
ENV TERRAFORM_VERSION=${terraform_version_arg}
ENV TERRAGRUNT_VERSION=${terragrunt_version_arg}
ENV AMI_MANAGER_VERSION=${ami_manager_arg}
ENV NODE_VERSION=${node_version_arg}
ENV PYTHON_PIP_VERSION=${pip_install_version}

# set up nodejs repo
RUN curl -sL https://rpm.nodesource.com/setup_${NODE_VERSION} | bash -

RUN yum update -y && \
    yum install -y wget zip unzip && \
    yum install -y https://repo.ius.io/ius-release-el7.rpm && \
    yum install -y python36u && \
    yum install -y python36u-pip && \
    yum install -y openssh-clients && \
    yum install -y jq && \
    yum install -y git && \
    yum install -y nodejs

WORKDIR /root/workspace
# this variable is used to run packer
ENV USER ec2-user

# install packer and create an symlink on /usr/local
RUN wget https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip
RUN unzip /root/workspace/packer_${PACKER_VERSION}_linux_amd64.zip -d /opt/packer/
RUN ln -s /opt/packer/packer /usr/local/bin/packer

# install packer plugins
RUN mkdir -p ~/.packer.d/plugins
RUN wget https://github.com/wata727/packer-post-processor-amazon-ami-management/releases/download/v${AMI_MANAGER_VERSION}/packer-post-processor-amazon-ami-management_${AMI_MANAGER_VERSION}_linux_amd64.zip -P /tmp/
RUN cd ~/.packer.d/plugins
RUN unzip -j /tmp/packer-post-processor-amazon-ami-management_${AMI_MANAGER_VERSION}_linux_amd64.zip -d ~/.packer.d/plugins

# install ansible
# RUN pip3.6 install --upgrade pip==21.1.3
RUN pip3 install --no-cache-dir --upgrade pip==${PYTHON_PIP_VERSION}
RUN pip3 install ansible==${ANSIBLE_VERSION}

# install terraform and create an symlink on /usr/local
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN unzip /root/workspace/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /opt/terraform
RUN ln -s /opt/terraform/terraform /usr/local/bin/terraform

# install terragrunt and create a symlink on /usr/local
RUN wget https://github.com/gruntwork-io/terragrunt/releases/download/v${TERRAGRUNT_VERSION}/terragrunt_linux_amd64
RUN mkdir -p /opt/terragrunt && mv terragrunt_linux_amd64 /opt/terragrunt/terragrunt
RUN chmod +x /opt/terragrunt/terragrunt
RUN ln -s /opt/terragrunt/terragrunt /usr/local/bin/terragrunt

# install pip packages
RUN pip3 install boto3 sh argparse awscli pytz

# install ansible-galaxy packages
COPY requirements.yml /tmp/
RUN ansible-galaxy install --roles-path /etc/ansible/roles -r /tmp/requirements.yml 
