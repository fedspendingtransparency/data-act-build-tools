#!/bin/bash

aws s3 cp s3://$CONFIG_BUCKET_NAME/$CONFIG_FILE_KEY /etc/nginx/conf.d/

aws ssm get-parameter --name $PUBLIC_CERT_PARAM_NAME --with-decryption --output text --query Parameter.Value --region us-gov-west-1 > /etc/nginx/ssl/public.pem || true
aws ssm get-parameter --name $PRIVATE_KEY_PARAM_NAME --with-decryption --output text --query Parameter.Value --region us-gov-west-1 > /etc/nginx/ssl/private.pem || true

nginx -g "daemon off;"