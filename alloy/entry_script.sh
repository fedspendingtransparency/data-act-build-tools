#!/bin/bash

# At runtime, determine the IP address assigned to this ECS Task.
ECS_IPV4=$(curl -s $ECS_CONTAINER_METADATA_URI_V4 | jq -r '.Networks[0].IPv4Addresses[0]')

exec alloy run \
  --disable-reporting \
  --server.http.listen-addr=0.0.0.0:12345 \
  --cluster.advertise-address="$ECS_IPV4" \
  --cluster.enabled=true \
  --cluster.rejoin-interval="30s" \
  --cluster.discover-peers="provider=aws service=ecs ecs_cluster=usas-monitoring-$ENV_DISPLAYNAME addr_type=private_v4 region=us-gov-west-1 tag_key=cluster_id tag_value=$ENV_DISPLAYNAME"\
  /etc/alloy/config.alloy