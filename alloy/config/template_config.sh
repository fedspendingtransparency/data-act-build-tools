#!/bin/bash

proxy=${1}
BRANCH_NAME=${2}
FEATURE_BRANCH=${3:-false}
TEMPLATE=${4:-'blackbox_template.yml'}
TEMPLATE=${5:-'config.alloy'}

export HTTP_PROXY=${proxy}

if $FEATURE_BRANCH; then
  export ENV_DISPLAYNAME=`echo -n $BRANCH_NAME | sha1sum | cut -c1-8`
else
  export ENV_DISPLAYNAME="admin"
fi

rm -f blackbox.yml temp.yml
( echo "cat <<EOF >blackbox.yml";
  cat blackbox_template.yml;
  echo "EOF";
) >temp.yml
. temp.yml

rm -f config.alloy temp.alloy
( echo "cat <<EOF >config.alloy";
  cat template.alloy;
  echo "EOF";
) >temp.alloy
. temp.alloy

rm -f temp.yml
