FROM centos:7

RUN yum update -y && yum clean all

##### Python prereqs
RUN yum -y install wget make zip gcc openssl-devel bzip2-devel libffi-devel zlib-devel xz-devel 

##### Building python 3.7
WORKDIR /usr/src
RUN wget --quiet https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz
RUN tar xzf Python-3.7.3.tgz
WORKDIR /usr/src/Python-3.7.3
RUN ./configure --enable-optimizations
RUN make altinstall
RUN ln -sf /usr/local/bin/python3.7 /usr/bin/python3
RUN echo "$(python3 --version)"


RUN yum -y install https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
RUN yum -y install postgresql13

RUN python3 -m pip install awscli