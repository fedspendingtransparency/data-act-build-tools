FROM centos:7

RUN yum install -y epel-release \
    yum makecache fast \
    yum install -y python3-devel zlib-devel libpqxx postgresql-devel gcc
    
RUN pip3 install PyGreSQL PyYAML requests boto3