import boto3
import json
import argparse
import sys
import shutil
import os
from subprocess import Popen, PIPE

EXIT_CODE = 0

# global boto connection
ec2_client = boto3.client('ec2', region_name='us-gov-west-1')

def deploy():

    # This tf_var file is expected to be copied from an external source
    tfvar_file   = 'usaspending-bulk-download-vars.tf.json'

    tf_exec_path = 'terraform'
    tf_file      = 'usaspending-bulk-download-deploy.tf'

    parser = argparse.ArgumentParser()
    parser.add_argument('--deploy_env', required=True, choices=['sandbox', 'dev', 'staging', 'prod'])
    args = parser.parse_args()
    deploy_env = args.deploy_env

    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()

    #initialize variables needed to deploy terraform
    tf_state_s3_bucket = tfvar_data['variable']['tf_state_s3_bucket']['default']
    tf_state_s3_path = tfvar_data['variable']['tf_state_s3_path']['default']
    tf_aws_region = tfvar_data['variable']['aws_region']['default']

    # Get previously created API AMI (created by usaspending-deploy.py)
    current_api_ami = ec2_client.describe_images(Filters=[
        {'Name':'tag:current', 'Values':['True']},
        {'Name':'tag:base', 'Values':['False']},
        {'Name':'tag:type', 'Values':['USASpending-API']},
        {'Name':'tag:environment', 'Values':[deploy_env]}
        ])['Images'][0]['ImageId']

    # Add API AMI to Terraform variables
    update_tf_ami(current_api_ami, tfvar_file)

    print('**************************************************************************')
    print(' Running terraform... ')
    # Terraform appears to be pretty particular about variable and .tf files, so move the ones we need into
    # a subdir so this doesn't have to happen via Jenkins.
    shutil.rmtree(deploy_env, ignore_errors=True)
    os.mkdir(deploy_env)
    shutil.copy(tf_file,    deploy_env)
    shutil.copy(tfvar_file, deploy_env)
    os.chdir(deploy_env)

    # Run Terraform plan and apply
    real_time_command([tf_exec_path, 'init',  '-input=false',
                       '-backend-config=bucket='+tf_state_s3_bucket,
                       '-backend-config=key='+tf_state_s3_path,
                       '-backend-config=region='+tf_aws_region])
    real_time_command([tf_exec_path, 'plan',  '-input=false', '-out=' + tf_file])
    real_time_command([tf_exec_path, 'apply', '-input=false', tf_file])

    global EXIT_CODE
    if EXIT_CODE != 0:
        print('Exiting with a code of {}'.format(EXIT_CODE))
        sys.exit(EXIT_CODE)

###############################################################################
# Helper Functions
###############################################################################

def real_time_command(command_to_run):
    process = Popen(command_to_run, stdout=PIPE)
    total_output = ''
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:
            break
        if output:
            total_output += output

            # Pretty-print human readable output
            if '-machine-readable' in command_to_run:
                output = output[output.rfind(',') + 1:]
            print(output.strip())

    rc = process.poll()
    global EXIT_CODE
    EXIT_CODE += rc

    return total_output


def update_tf_ami(new_ami='', tfvar_file='variables.tf.json'):
    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()

    tfvar_data['variable']['aws_amis']['default']['us-gov-west-1'] = new_ami

    tfvar_json = open(tfvar_file, "w+")
    tfvar_json.write(json.dumps(tfvar_data, indent=4))
    tfvar_json.close()

    print ('Updated ' + tfvar_file + ' with AMI id ' + new_ami)

    return


if __name__ == '__main__':
    deploy()
