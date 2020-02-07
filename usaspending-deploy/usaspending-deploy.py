import boto3
import os
import json
import argparse
import sys
import shutil
from subprocess import Popen, PIPE

EXIT_CODE = 0

# global boto connections
ec2_client = boto3.client('ec2', region_name='us-gov-west-1')
ec2_resource = boto3.resource('ec2', region_name='us-gov-west-1')


def deploy():

    # This tf_var file is expected to be copied from an external source
    tfvar_file       = 'usaspending-vars.tf.json'
    tf_exec_path     = 'terraform'
    tf_file          = 'usaspending-deploy.tf'

    packer_exec_path = 'packer'
    packer_file      = 'usaspending-packer.json'

    parser = argparse.ArgumentParser()
    parser.add_argument('--deploy_env', required=True, choices=['sandbox', 'dev', 'staging', 'prod'])
    args = parser.parse_args()
    deploy_env = args.deploy_env

    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()

    # Initialize variables needed to deploy terraform
    tf_state_s3_bucket = tfvar_data['variable']['tf_state_s3_bucket']['default']
    tf_state_s3_path = tfvar_data['variable']['tf_state_s3_path']['default']
    tf_aws_region = tfvar_data['variable']['aws_region']['default']
    startup_script = "usaspending-start-{}.sh".format(deploy_env)

    # Get Old AMIs, for setting current=False after new one is created
    old_instance_amis = ec2_client.describe_images(Filters=[
        {'Name':'tag:current', 'Values':['True']},
        {'Name':'tag:base', 'Values':['False']},
        {'Name':'tag:type', 'Values':['USASpending-API']},
        {'Name':'tag:environment', 'Values':[deploy_env]}
        ])['Images']

    print("Old Instance AMIs: ")
    print(old_instance_amis)

    # Build New AMI (Packer)
    print('**************************************************************************')
    print(' Building new AMI via Packer. This can take a while...')

    packer_output = real_time_command([packer_exec_path, 'build -debug', 
                                      '-var', 'environment_ami_tag={}'.format(deploy_env), 
                                      '-var', 'ansible_branch_var={}'.format('master' if deploy_env == 'prod' else deploy_env), 
                                      '-machine-readable', packer_file])
    ami_line = [line for line in packer_output.split('\n') if "amazon-ebs: AMIs were created:" in line][0]
    new_instance_ami = ami_line[ami_line.find('ami-'):ami_line.find('ami-')+12]
    print('Done. New AMI created: ' + new_instance_ami)

    # Set current=False tag for old AMIs
    if old_instance_amis:
        print('Done. Setting current tag to False on old instance AMIs: \n' + '\n'.join(map(str, old_instance_amis)) )
        update_ami_tags(old_instance_amis)
        print('Done.')
    else:
        print('No matching old AMIs. Skipping tag update...')

    # Add new AMI to Terraform variables
    # Variable aws_amis now replaced with newly created ami-id 
    update_tf_ami(new_instance_ami, tfvar_file)

    # Update Terraform User Data
    update_terraform_user_data(deploy_env)

    print('**************************************************************************')
    print(' Running terraform... ')
    # Terraform appears to be pretty particular about variable and .tf files, so move the ones we need into
    # a subdir so this doesn't have to happen via Jenkins.
    shutil.rmtree(deploy_env, ignore_errors=True)
    os.mkdir(deploy_env)
    shutil.copy(tf_file,    deploy_env)
    shutil.copy(tfvar_file, deploy_env)
    shutil.copy(startup_script, deploy_env)
    os.chdir(deploy_env)

    # Run Terraform plan and apply
    # Terraform now builds out usaspending_api and usaspending_bd 
    # as both are now contained within the single usaspending-deploy.tf file
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


def update_terraform_user_data(environment='staging', tf_file='usaspending-deploy.tf'):
    f = open(tf_file,'r')
    filedata = f.read()
    f.close()

    # environment = prod, staging, dev, or sandbox
    startup_shell_script = "usaspending-start-{}.sh".format(environment)
    newdata = filedata.replace("usaspending-start-staging.sh", startup_shell_script)

    f = open(tf_file,'w')
    f.write(newdata)
    f.close()

    print ('Updated ' + tf_file + ' with user data script for ' + environment)

    return


def update_ami_tags(old_instance_amis):
    for ami in old_instance_amis:
        image = ec2_resource.Image(ami['ImageId'])
        image.create_tags(
            DryRun=False,
            Tags=[{'Key': 'current', 'Value': 'False'}]
        )
    return


if __name__ == '__main__':
    deploy()
