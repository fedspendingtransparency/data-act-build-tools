#!/bin/bash

proxy=${1}
BRANCH_NAME=${1}
FEATURE_BRANCH=${3:-false}
TEMPLATE=${4:-'prometheus_template.yml'}

export HTTP_PROXY=${proxy}

if $FEATURE_BRANCH; then
  export ENV_DISPLAYNAME=`echo -n $BRANCH_NAME | sha1sum | cut -c1-8`
else
  export ENV_DISPLAYNAME=$BRANCH_NAME
fi

rm -f prometheus.yml temp.yml
( echo "cat <<EOF >prometheus.yml";
  cat prometheus_template.yml;
  echo "EOF";
) >temp.yml
. temp.yml

rm -f temp.yml
