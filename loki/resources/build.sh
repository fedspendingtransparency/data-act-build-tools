#!/bin/bash

# Insert this script into the components dir that you want to build, tag, and push
# Names of the images:
# Daemon    - av_daemon
# Api       - av_api
# Names of the ECR Repos:
# Daemon    - dti-tooling-av-daemon-{environment}
# Api       - dti-tooling-av-api-{environment}

PUSH=${1:-'false'}
LOGIN=${2:-'false'}
CACHE=${3:-'true'}

if [[ $LOGIN == 'true' ]]
then
    aws ecr get-login-password --region us-gov-west-1 | docker login --username AWS --password-stdin 807618423734.dkr.ecr.us-gov-west-1.amazonaws.com
fi

if [[ $CACHE == 'false' ]]
then
    (
        cd .. && \
        docker build --no-cache -t loki \
            --build-arg HTTP_PROXY=http://j1proxy.frb.org:8080 \
            --build-arg HTTPS_PROXY=http://j1proxy.frb.org \
            --build-arg NO_PROXY=.frb.pvt \
            --build-arg PROXY_URL=https://dticnlb101-a829a11464caaa9a.elb.us-gov-west-1.amazonaws.com \
            .
    )
else
    (
        cd .. && \
        docker build -t loki \
            --build-arg HTTP_PROXY=http://j1proxy.frb.org:8080 \
            --build-arg HTTPS_PROXY=http://j1proxy.frb.org \
            --build-arg NO_PROXY=.frb.pvt \
            --build-arg PROXY_URL=https://dticnlb101-a829a11464caaa9a.elb.us-gov-west-1.amazonaws.com \
            .
    )
fi

if [[ $PUSH == 'true' ]]
then
    docker tag loki:latest 807618423734.dkr.ecr.us-gov-west-1.amazonaws.com/dti/monitoring/loki:latest
    docker push 807618423734.dkr.ecr.us-gov-west-1.amazonaws.com/dti/monitoring/loki:latest
fi
