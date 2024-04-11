#!/bin/bash

proxy=${1}
TEMPLATE=${3:-'prometheus_template.yml'}

export HTTP_PROXY=${proxy}

rm -f prometheus.yml temp.yml
( echo "cat <<EOF >prometheus.yml";
  cat prometheus_template.yml;
  echo "EOF";
) >temp.yml
. temp.yml

rm -f temp.yml
