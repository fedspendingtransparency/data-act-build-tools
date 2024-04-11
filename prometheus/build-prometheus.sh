#!/bin/bash

BRANCH=${GIT_BRANCH:-"$(git branch --show-current)"}
ACCOUNT=${1}
TOKEN=`aws ssm get-parameter --name /jenkins/service/api-token --with-decryption --output text --query Parameter.Value --region us-gov-west-1`

docker build -t $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/monitoring/prometheus:$BRANCH --build-arg token=$TOKEN -f Dockerfile .
docker push $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/monitoring/prometheus:$BRANCH