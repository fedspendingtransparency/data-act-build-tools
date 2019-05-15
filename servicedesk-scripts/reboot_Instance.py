import boto3
import time
import sys
import logging


region = 'us-east-1'

def main():
    session = boto3.Session(profile_name='marouane')

    elb = session.client('elb', region_name=region)
    instance = elb.describe_load_balancers(LoadBalancerNames=[
        'servicedesk-dev',
    ])['LoadBalancerDescriptions'][0]['Instances'][0]['InstanceId']
    ec2 = session.client('ec2', region_name=region)
    ec2.reboot_instances(InstanceIds=[instance, ])
    print('instance rebooted with Instance ID: ' + instance)
    elb_check = elb.describe_instance_health(
        LoadBalancerName='servicedesk-dev',
    )
    # Wait for the ELB health check to turn OutOfService
    time.sleep(60)

    tries  = 0
    maxtries = 10
    status = None
    # wait fir the health check to become InService

    while (tries < maxtries ):

        status = elb_check.get("InstanceStates")[0].get("State")
        if (status != "OutOfService"):
            break
        time.sleep(60)
        tries += 1
        print(tries)

    if (status == "OutOfService" and tries == maxtries):
        sys.exit(1)

if __name__ == '__main__':
	main()

