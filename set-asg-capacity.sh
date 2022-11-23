#!/bin/bash

# DESCRIPTION: sets an autoscaling group to a desired capacity. Synchronously waits for group to meet capacity.
# USAGE: ./set-desired-capacity.sh ENVIRONMENT APPLICATION COMPONENT CAPACITY <INTERVAL> <RETRIES>

environment=$1
application=$2
component=$3
capacity=$4
interval=${5:-5}
retries=${6:-120}

sample_instance_id=$(aws ec2 describe-instances \
--filters \
    "Name=tag:Application, Values=$application" \
    "Name=tag:Component, Values=$component" \
    "Name=tag:Environment,Values=$environment" \
--region us-gov-west-1 \
--query Reservations[*].Instances[*].[InstanceId] \
--output text | head -n 1)

echo sample instance_id: $sample_instance_id

if [ -z "${sample_instance_id}" ]
then
    echo no instances found
    exit;
fi

autoscaling_group="$(aws autoscaling describe-auto-scaling-instances \
    --instance-ids $sample_instance_id \
    --query AutoScalingInstances[0].AutoScalingGroupName \
    --region us-gov-west-1 \
    --output text)"

echo autoscaling group: $autoscaling_group

if [ -z "${autoscaling_group}" ]
then
    echo no autoscaling group found
    exit;
fi

if [ $capacity -eq 0 ]
then
    echo capacity is 0 so making sure autoscaling group can support 0 instances
    aws autoscaling update-auto-scaling-group \
        --auto-scaling-group-name "${autoscaling_group}" \
        --min-size 0 --region us-gov-west-1
fi

aws autoscaling set-desired-capacity \
    --auto-scaling-group-name "${autoscaling_group}" \
    --desired-capacity $capacity --region us-gov-west-1

num_instances=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "${autoscaling_group}" \
    --region us-gov-west-1 \
    --query AutoScalingGroups[0].Instances \
    --output text | wc -l)

while [ $num_instances -ne $capacity ] && [ $retries -gt 0 ]
do
    let "retries--"
    echo there are $num_instances instances running. sleeping $interval seconds and will retry $retries more times...
    sleep $interval
    num_instances=$(aws autoscaling describe-auto-scaling-groups \
        --auto-scaling-group-names "${autoscaling_group}" \
        --region us-gov-west-1 \
        --query AutoScalingGroups[0].Instances \
        --output text | wc -l)
done

echo autoscaling group "${autoscaling_group}" has reached $capacity instances
