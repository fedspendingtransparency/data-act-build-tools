#!/bin/bash

BRANCH_NAME=${GIT_BRANCH:-"$(git branch --show-current)"}
ACCOUNT=${1}
proxy=${2}
FEATURE_BRANCH=${3:-false}

if $FEATURE_BRANCH; then
  export ENV_DISPLAYNAME=`echo -n $BRANCH_NAME | sha1sum | cut -c1-8`
else
  export ENV_DISPLAYNAME="latest"
fi

docker build -t $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/grafana:$ENV_DISPLAYNAME --build-arg HTTPS_PROXY=${proxy} --build-arg HTTP_PROXY=${proxy} -f Dockerfile .
docker push $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/grafana:$ENV_DISPLAYNAME