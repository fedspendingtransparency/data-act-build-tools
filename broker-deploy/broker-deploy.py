import boto3
import os
import json
import argparse
import sys
import shutil
from subprocess import Popen, PIPE


EXIT_CODE = 0
# set global boto connection
ec2_client = boto3.client('ec2', region_name='us-gov-west-1')
ec2_resource = boto3.resource('ec2', region_name='us-gov-west-1')


def deploy():

    # set paths
    packer_file = 'broker-packer.json'
    tfvar_file = 'broker-vars.tf.json'
    tf_file = 'broker-deploy.tf'
    packer_exec_path = 'packer'
    tf_exec_path = 'terraform'

    parser = argparse.ArgumentParser()
    parser.add_argument('--deploy_env', required=True, choices=['sandbox', 'dev', 'staging', 'prod'])
    args = parser.parse_args()
    deploy_env = args.deploy_env

    tfvar_file = deploy_env + '-variables.tf.json'
    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()

    # initialize variables needed to deploy terraform
    tf_state_s3_bucket = tfvar_data['variable']['tf_state_s3_bucket']['default']
    tf_state_s3_path = tfvar_data['variable']['tf_state_s3_path']['default']
    tf_aws_region = tfvar_data['variable']['aws_region']['default']

    # Retrieve current Base app AMI (where type=app and current=true)
    print('Retrieving current base app AMI...')
    current_base_ami = get_current_base_ami()

    # Insert current Base app AMI into packer file
    print('Updating Packer file with current base app AMI ' + current_base_ami + '...')
    update_packer_spec(packer_file, current_base_ami, deploy_env)
    print('Done.')

    # Retrieve current App Instance AMIs
    print('Retrieving current app instance AMI(s)...')
    current_app_amis = get_current_app_instance_amis(deploy_env)

    print('Done. Current app instance AMI(s): '+ '\n'.join(map(str, current_app_amis)) )

    # Build new app instance AMI via Packer
    print('**************************************************************************')
    print('Buiding new app instance AMI via Packer. This may take a few minutes...')
    packer_output = real_time_command([packer_exec_path, 'build', packer_file, '-machine-readable'])
    ami_line = [line for line in packer_output.split('\n') if "amazon-ebs: AMIs were created:" in line][0]
    ami_id = ami_line[ami_line.find('ami-'):ami_line.find('ami-')+12]
    print('Done. Packer AMI created: '+ami_id)

    # Set current=False tag for old App AMIs
    if current_app_amis:
        print('Setting current tag to False on old instance AMIs: \n' + '\n'.join(map(str, current_app_amis)) )
        update_ami_tags(current_app_amis)
        print('Done.')
    else:
        print('No matching old AMIs. Skipping tag update...')

    # Confirm app instance that was created is now only current=True tagged AMI
    new_ami = ec2_client.describe_images(Filters=[
            {'Name':'tag:current', 'Values':['True']},
            {'Name':'tag:base', 'Values':['False']},
            {'Name':'tag:type', 'Values':['Application']},
            {'Name':'tag:environment', 'Values':[deploy_env]}
            ])['Images'][0]['ImageId']
    if ami_id == new_ami:
        print('Success! Packer AMI id matches current tagged AMI.')
    else:
        print('Something went wrong. Packer AMI: '+ami_id+'; Tagged AMI: '+ new_ami)

    # Add new AMI id to terraform variables
    update_lc_ami(ami_id, tfvar_file, deploy_env)

    print('**************************************************************************')
    print(' Running terraform... ')
    # Terraform appears to be pretty particular about variable and .tf files, so move the ones we need into
    # a subdir so this doesn't have to happen via Jenkins. If someone can figure out how to point TF init
    # to a custom file/variable ...
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

def get_current_base_ami():
    base_ami = ec2_client.describe_images(Filters=[
        {'Name':'tag:current', 'Values':['True']},
        {'Name':'tag:base', 'Values':['True']},
        {'Name':'tag:type', 'Values':['Application']}
        ])['Images'][0]['ImageId']

    return base_ami

def get_current_app_instance_amis(deploy_env):
    app_instance_amis = ec2_client.describe_images(Filters=[
        {'Name':'tag:current', 'Values':['True']},
        {'Name':'tag:base', 'Values':['False']},
        {'Name':'tag:type', 'Values':['Application']},
        {'Name':'tag:environment', 'Values':[deploy_env]}
        ])['Images']
    return app_instance_amis

def real_time_command(command_to_run):
    process = Popen(command_to_run, stdout=PIPE)
    total_output = ''
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:
            break
        if output:
            total_output += output

            if '-machine-readable' in command_to_run:
                output = output[output.rfind(',') + 1:]
            print(output.strip())

    rc = process.poll()
    global EXIT_CODE
    EXIT_CODE += rc

    return total_output

def update_packer_spec(packer_file, current_base_ami, environment):
    packer_json = open(packer_file, "r")
    packer_data = json.load(packer_json)
    packer_json.close()

    packer_data['builders'][0]['source_ami'] = current_base_ami
    packer_data['builders'][0]['tags']['environment'] = environment

    # dev branch is called development, prod means master branch
    if environment == 'dev':
        environment = 'development'
    if environment == 'prod':
        environment = 'master'
    packer_data['provisioners'][0]['extra_arguments'] = ["--extra-vars",
     "BRANCH={} HOST=local".format(environment) ]

    packer_json = open(packer_file, "w+")
    packer_json.write(json.dumps(packer_data, indent=4, sort_keys=True))
    packer_json.close()

    return

def update_lc_ami(new_ami='', tfvar_file='variables.tf.json', deploy_env='na'):
    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()
    tfvar_data['variable']['aws_amis']['default']['us-gov-west-1'] = new_ami
    tfvar_json = open(tfvar_file, "w+")
    tfvar_json.write(json.dumps(tfvar_data, indent=4))
    tfvar_json.close()

    return

def update_ami_tags(current_app_amis):
    for ami in current_app_amis:
        image = ec2_resource.Image(ami['ImageId'])
        print("updating: " + ami['ImageId'])
        image.create_tags(
            DryRun=False,
            Tags=[{'Key': 'current', 'Value': 'False'}]
        )
    return


if __name__ == '__main__':
    deploy()
