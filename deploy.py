import boto
from boto import ec2
import sh
import os
import json
import argparse
import sys

def deploy():

    # set paths
    packer_file = 'packer.json'
    tfvar_file = 'variables.tf.json'
    packer_exec_path = '/packer/packerio'
    tf_exec_path = '/terraform/terraform'


    #Set connection
    print('Connecting to AWS via region us-gov-west-1...')
    conn = boto.ec2.connect_to_region(region_name='us-gov-west-1')
    print('Done.')

    parser = argparse.ArgumentParser()

    parser.add_argument("-dev", "--dev", action="store_true", help="Runs deploy for dev")
    parser.add_argument("-stg", "--staging", action="store_true", help="Runs deploy for staging")
    parser.add_argument("-prod", "--prod", action="store_true", help="Runs deploy for prod")
    args = parser.parse_args()
    optionsDict = vars(args)
    noArgs = True

    for arg in optionsDict:
        if(optionsDict[arg]):
            noArgs = False

    if noArgs:
        print ("No environment specified. Please include an argument: --dev, --staging, or --prod")
        sys.exit(1)

    if optionsDict["dev"]:
        deploy_env = 'dev'
    elif optionsDict["staging"]:
        deploy_env = 'staging'
        # Retrieve current App Instance AMIs
        print('Retrieving current app instance AMI(s)...')
        current_app_amis = conn.get_all_images(filters={"tag:current" : "True", "tag:base" : "False", "tag:type" : "Application", "tag:environment" : deploy_env})
        print('Done. Current app instance AMI(s): '+ '\n'.join(map(str, current_app_amis)) )

        # Retrieve current Base app AMI (where type=app and current=true)
        print('Retrieving current base app AMI...')
        current_base_ami = conn.get_all_images(filters={"tag:current" : "True", "tag:base" : "True", "tag:type" : "Application"})[0].id
        print('Done. Current base app AMI: '+current_base_ami)

        # Insert current Base app AMI into packer file
        print('Updating Packer file with current base app AMI...')
        update_packer_spec(packer_file, current_base_ami)
        print('Done.')

        # Build new app instance AMI via Packer
        print('Buiding new app instance AMI via Packer. This may take a few minutes...')
        packer_output = packer_build(packer_file, packer_exec_path)
        ami_line = [line for line in packer_output.split('\n') if "amazon-ebs: AMIs were created:" in line][0]
        ami_id = ami_line[ami_line.find('ami-'):ami_line.find('ami-')+12]
        print('Done. Packer AMI created: '+ami_id)

        # Set current=False tag for old App AMIs
        print('Setting current tag to False on old app instance AMIs')
        update_ami_tags(current_app_amis)
        print('Done')

        # Confirm app instance that was created is now only current=True tagged AMI
        if ami_id == conn.get_all_images(filters={"tag:current" : "True", "tag:base" : "False", "tag:type" : "Application", "tag:environment" : deploy_env})[0].id:
            print('Success! Packer AMI id matches current tagged AMI.')
        else:
            print('Something went wrong. Packer AMI: '+ami_id+'; Tagged AMI: '+conn.get_all_images(filters={"tag:current" : "True", "tag:base" : "False", "tag:type" : "Application", "tag:environment" : deploy_env})[0].id)

        #Add new AMI id to terraform variables
        update_lc_ami(ami_id, tfvar_file)

        #Run terraform
        run_tf(tf_exec_path)

    elif optionsDict["prod"]:
        #For prod, we don't build a new artifact, we just run terraform against the current staging AMI
        deploy_env = 'prod'
        # get current staging AMI
        staging_ami = conn.get_all_images(filters={"tag:current" : "True", "tag:base" : "False", "tag:type" : "Application", "tag:environment" : "staging"})[0].id
        # Update terraform variables with staging ami_id
        update_lc_ami(staging_ami, 'variables.tf.json')
        print(staging_ami)
        #Rune terraform
        run_tf(tf_exec_path)


def run_tf(tf_exec_path):
    # Run terraform
    plan_output = tf_plan(tf_exec_path)
    print(plan_output)
    apply_output = tf_apply(tf_exec_path)
    print(apply_output)
    return


def packer_build(packer_file='packer.json', packer_exec_path='packer'):
    cmd = sh.Command(packer_exec_path).build.bake(packer_file).bake('-machine-readable')
    return cmd()

def tf_plan(tf_exec_path):
    cmd = sh.Command(tf_exec_path).plan
    return cmd()

def tf_apply(tf_exec_path):
    cmd = sh.Command(tf_exec_path).apply
    return cmd()

def update_packer_spec(packer_file='packer.json', current_base_ami=''):
    packer_json = open(packer_file, "r")
    packer_data = json.load(packer_json)
    packer_json.close()

    packer_data['builders'][0]['source_ami'] = current_base_ami

    packer_json = open(packer_file, "w+")
    packer_json.write(json.dumps(packer_data))
    packer_json.close()

    return

def update_lc_ami(new_ami='', tfvar_file='variables.tf.json'):
    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()

    tfvar_data['variable']['aws_amis']['default']['us-gov-west-1'] = new_ami

    tfvar_json = open(tfvar_file, "w+")
    tfvar_json.write(json.dumps(tfvar_data))
    tfvar_json.close()

    return

def update_ami_tags(current_app_amis=False):
    for ami in current_app_amis:
        ami.remove_tag('current','True')
        ami.add_tag('current','False')

    return


if __name__ == '__main__':
    deploy()