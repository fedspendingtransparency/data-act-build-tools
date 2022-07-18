FROM centos:7

RUN yum install -y epel-release \
    yum makecache fast \
    yum install -y python3-devel zlib-devel libpqxx postgresql-devel gcc \
    yum clean all
    
RUN python3 -m pip install PyGreSQL PyYAML requests boto3 ruamel.yaml ansible==2.9.27