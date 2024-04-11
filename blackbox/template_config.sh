#!/bin/bash

proxy=${1}
TEMPLATE=${2:-'blackbox_template.yml'}

export HTTP_PROXY=${proxy}

rm -f blackbox.yml temp.yml
( echo "cat <<EOF >blackbox.yml";
  cat blackbox_template.yml;
  echo "EOF";
) >temp.yml
. temp.yml

rm -f temp.yml
