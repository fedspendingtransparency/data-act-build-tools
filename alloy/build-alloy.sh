#!/bin/bash

BRANCH=${GIT_BRANCH:-"$(git branch --show-current)"}
ACCOUNT=${1}
FEATURE_BRANCH=${2:-false}
TOKEN=`aws ssm get-parameter --name /jenkins/service/api-token --with-decryption --output text --query Parameter.Value --region us-gov-west-1`

rm -rf /config/template-config.sh
if $FEATURE_BRANCH; then
  export ENV_DISPLAYNAME=`echo -n $BRANCH_NAME | sha1sum | cut -c1-8`
else
  export ENV_DISPLAYNAME="latest"
fi

docker build -t $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/alloy:$ENV_DISPLAYNAME --build-arg token=$TOKEN -f Dockerfile .
docker push $ACCOUNT.dkr.ecr.us-gov-west-1.amazonaws.com/alloy:$ENV_DISPLAYNAME