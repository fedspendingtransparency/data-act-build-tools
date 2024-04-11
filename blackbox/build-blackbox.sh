#!/bin/bash

BRANCH=${GIT_BRANCH:-"$(git branch --show-current)"}
ACCOUNT=${1}

docker build -t $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/blackbox:latest -f Dockerfile .
docker push $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/blackbox:latest