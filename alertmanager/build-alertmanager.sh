#!/bin/bash

BRANCH=${GIT_BRANCH:-"$(git branch --show-current)"}
ACCOUNT=${1}

./template_config.sh feature_template.yml

docker build -t $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/alertmanager:latest -f Dockerfile .
docker push $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/alertmanager:latest
