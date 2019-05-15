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

    minutes  = 0
    maxtime = 10
    status = None
    # wait fir the health check to become InService

    while (minutes < maxtime ):

        status = get_elb_status(elbname, elb).get("InstanceStates")[0].get("State")
    
        if (status != "OutOfService"):
            break
        time.sleep(60)
        tries += 1
        print("The instance status is {} after {} minute(s)".format (status, minutes))

    if (status == "OutOfService" and minutes == maxtime):
        sys.exit(1)


def get_elb_status(elbname, elb):
    status = elb.describe_instance_health(LoadBalancerName=elbname,)
    return status

if __name__ == '__main__':
	main()

