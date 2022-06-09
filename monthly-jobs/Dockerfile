FROM python:3.7-slim

# Install relevant packages for USAspending and Broker functionality
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

# Pip install packages needed for USAspending and Broker
RUN pip install awscli