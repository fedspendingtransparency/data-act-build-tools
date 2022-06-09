FROM python:3.7-slim

# Image mostly copied from monthly-pruner
RUN apt-get update -y && apt-get install -y \
    git \
    postgresql-client-13 \
    libffi-dev \
    g++ \
    wget \
    mlocate \
    zlib1g-dev \
    libbz2-dev \
    unzip \
    zip \
    python3-memcache \
    libmemcached-dev

RUN pip install boto3 sh argparse psycopg2-binary==2.7.5 setuptools awscli