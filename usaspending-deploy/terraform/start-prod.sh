#!/bin/bash

# Grab the private IP for ALLOWED_HOSTS
export PVT_IP=`ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/'`

sudo ansible-playbook /tmp/ansible-dir/usaspending-api-launch.yml -c local \
--extra-vars "HOST=localhost" \
--extra-vars "ALLOWED_HOSTS='spending-api.us','$PVT_IP'" \
--extra-vars "BRANCH=master" \
--extra-vars "DOMAIN=spending-api.us"
