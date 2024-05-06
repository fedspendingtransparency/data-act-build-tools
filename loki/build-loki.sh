#!/bin/bash

BRANCH_NAME=${GIT_BRANCH:-"$(git branch --show-current)"}
ACCOUNT=${1}
FEATURE_BRANCH=${2:-false}

if $FEATURE_BRANCH; then
  export ENV_DISPLAYNAME=`echo -n $BRANCH_NAME | sha1sum | cut -c1-8`
else
  export ENV_DISPLAYNAME="latest"
fi

docker build -t $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/loki:$ENV_DISPLAYNAME -f Dockerfile .
docker push $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/loki:$ENV_DISPLAYNAME