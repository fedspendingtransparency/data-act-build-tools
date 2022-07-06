FROM centos:7

RUN rpm --import https://download.postgresql.org/pub/repos/yum/RPM-GPG-KEY-PGDG; \
    yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm; \
    yum install -y epel-release; \
    yum makecache fast

RUN yum install -y python3-devel zlib-devel libpqxx postgresql13-devel gcc; \
    yum clean all
    
RUN pip3 install PyGreSQL PyYAML requests boto3 ruamel.yaml