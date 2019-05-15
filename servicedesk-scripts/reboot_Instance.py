import boto3
import time
import sys
import argparse


region = 'us-east-1'

parser = argparse.ArgumentParser()
parser.add_argument('--elbname', required=True, type=str)
args = parser.parse_args()
elbname = args.elbname

def main():
    session = boto3.Session(profile_name='cf-invalidation')

    elb = session.client('elb', region_name=region)
    instance = elb.describe_load_balancers(LoadBalancerNames=[
        elbname,
    ])['LoadBalancerDescriptions'][0]['Instances'][0]['InstanceId']
    ec2 = session.client('ec2', region_name=region)
    ec2.reboot_instances(InstanceIds=[instance, ])
    print('instance rebooted with Instance ID: ' + instance)
    
    # Wait for the ELB health check to turn OutOfService
    time.sleep(60)

    tries  = 0
    maxtries = 10
    status = None
    # wait fir the health check to become InService

    while (tries < maxtries ):

        status = get_elb_status(elbname).get("InstanceStates")[0].get("State")
        print (status)
        if (status != "OutOfService"):
            break
        time.sleep(60)
        tries += 1
        print(tries)

    if (status == "OutOfService" and tries == maxtries):
        sys.exit(1)


def get_elb_status(elbname):
    status = elb.describe_instance_health(LoadBalancerName=elbname,)
    return status

if __name__ == '__main__':
	main()

