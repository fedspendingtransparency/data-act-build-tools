#!/bin/bash
#export SMTP_USERNAME=`(aws ssm get-parameter --name /ref/fiscal-service/mail-server/username --with-decryption --output text --query Parameter.Value --region us-gov-west-1)`
#export SMTP_PASSWORD=`(aws ssm get-parameter --name /ref/fiscal-service/mail-server/password --with-decryption --output text --query Parameter.Value --region us-gov-west-1)`

BRANCH_NAME=${1}
FEATURE_BRANCH=${2:-false}
TEMPLATE=${3:-'alertmanager_template.yml'}

if $FEATURE_BRANCH; then
  export ENV_DISPLAYNAME=`echo -n $BRANCH_NAME | sha1sum | cut -c1-8`
else
  export ENV_DISPLAYNAME=$BRANCH_NAME
fi

#if [ "$BRANCH_NAME" = "prod" ]; then
#    export EVERBRIDGE_SNS_ARN="arn:aws-us-gov:sns:us-gov-west-1:607927714227:dti-everbridge-payload-handler-$ENV_DISPLAYNAME"
#else
#    export EVERBRIDGE_SNS_ARN="arn:aws-us-gov:sns:us-gov-west-1:807618423734:dti-everbridge-payload-handler-$ENV_DISPLAYNAME"
#fi

rm -f alertmanager.yml temp.yml
( echo "cat <<EOF >alertmanager.yml";
  cat $TEMPLATE;
  echo "EOF";
) >temp.yml
. temp.yml

rm -f temp.yml