#!/bin/bash

proxy=${1}
BRANCH_NAME=${2}
FEATURE_BRANCH=${3:-false}
TEMPLATE=${4:-'config/blackbox_template.yml'}
TEMPLATE=${5:-'config/template.config'}

export HTTP_PROXY=${proxy}

if $FEATURE_BRANCH; then
  export ENV_DISPLAYNAME=`echo -n $BRANCH_NAME | sha1sum | cut -c1-8`
else
  export ENV_DISPLAYNAME="admin"
fi

rm -f blackbox.yml temp.yml
( echo "cat <<EOF >config/blackbox.yml";
  cat config/blackbox_template.yml;
  echo "EOF";
) >temp.yml
. temp.yml
