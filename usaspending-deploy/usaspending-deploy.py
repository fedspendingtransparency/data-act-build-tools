import boto
from boto import ec2
import sh
import os
import json
import argparse
import sys

def deploy():

    # Set config file and executable paths
    packer_file = 'packer.json'
    tfvar_file = 'variables.tf.json'
    packer_exec_path = '/Development/packer'
    tf_exec_path = '/Development/terraform/terraform'

    # Set connection
    print('Connecting to AWS via region us-gov-west-1...')
    conn = boto.ec2.connect_to_region(region_name='us-gov-west-1')
    print('Done.')

    parser = argparse.ArgumentParser()

    parser.add_argument("-stg", "--staging", 
        action="store_true", 
        help="Runs deploy for staging")
    parser.add_argument("-prod", "--prod", 
        action="store_true", 
        help="Runs deploy for prod")
    args = parser.parse_args()
    optionsDict = vars(args)
    noArgs = True

    for arg in optionsDict:
        if(optionsDict[arg]):
            noArgs = False

    if noArgs:
        print ("No environment specified. Please include an argument: --staging, or --prod")
        sys.exit(1)

    ### For staging, we make some changes to some files and run Packer

    if optionsDict["staging"]:
        deploy_env = 'staging'

  ###########################
  #      Packer Build       #
  ###########################

    #     print('Retrieving base AMI...')
    #     base_ami = conn.get_all_images(filters={
    #         "tag:current" : "True", 
    #         "tag:base"    : "True", 
    #         "tag:type"    : "USASpending-API"
    #         })[0].id
    #     print('Done. Updating Packer file to pull from base AMI: ' + base_ami + '...')
    #     update_packer_spec(packer_file, base_ami)
    #     print('Done.')

    #     print('**************************************************************************')
    #     print(' Building new app instance AMI via Packer. This can take a while...')
    #     packer_output = packer_build(packer_file, packer_exec_path)
    #     ami_line = [line for line in packer_output.split('\n') if "amazon-ebs: AMIs were created:" in line][0]
    #     new_instance_ami = ami_line[ami_line.find('ami-'):ami_line.find('ami-')+12]
    #     print('Done. Packer AMI created: ' + new_instance_ami)

    #     # Set current=False tag for old App AMIs
    #     print('Retrieving old instance AMI(s)...')
    #     old_instance_amis = conn.get_all_images(filters={ 
    #         "tag:current" : "True", 
    #         "tag:base"    : "False", 
    #         "tag:type"    : "USASpending-API", 
    #         "tag:environment" : "staging"
    #         })
    #     print('Done. Setting current tag to False on old instance AMIs: ' + '\n'.join(map(str, old_instance_amis)) )
    #     update_ami_tags(old_instance_amis)
    #     print('Done.')

    #     # Confirm AMI that was created is now only current=True tagged AMI
    #     staging_ami = conn.get_all_images(filters={
    #         "tag:current" : "True", 
    #         "tag:base"    : "False", 
    #         "tag:type"    : "Application", 
    #         "tag:environment" : "staging"
    #         })[0].id
    #     if new_instance_ami == staging_ami:
    #         print('Success! Packer AMI id matches current tagged AMI.')
    #     else:
    #         print('Something went wrong. New AMI: ' + new_instance_ami + '; Tagged AMI: ' + staging_ami)

    #     #Add new AMI id to Terraform variables
    #     update_lc_ami(new_instance_ami, tfvar_file)

    #     #Run Terraform
    #     run_tf(tf_exec_path)

    # elif optionsDict["prod"]:
    #     deploy_env = 'prod'

    #     # Just run Terraform against the current staging AMI
    #     staging_ami = conn.get_all_images(filters={
    #         "tag:current"     : "True", 
    #         "tag:base"        : "False", 
    #         "tag:type"        : "Application", 
    #         "tag:environment" : "staging"
    #         })[0].id

    #     # Update terraform variables with staging new_instance_ami
    #     update_lc_ami(staging_ami, 'variables.tf.json')

        # Run Terraform
        run_tf(tf_exec_path)


def run_tf(tf_exec_path):
    # Run Terraform
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

def tf_destroy(tf_exec_path):
    cmd = sh.Command(tf_exec_path).destroy.bake('-force')
    return cmd()

def tf_apply(tf_exec_path):
    cmd = sh.Command(tf_exec_path).apply
    return cmd()

def update_packer_spec(packer_file='packer.json', base_ami=''):
    packer_json = open(packer_file, "r")
    packer_data = json.load(packer_json)
    packer_json.close()

    packer_data['builders'][0]['source_ami'] = base_ami

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

    print ('Updated ' + tfvar_file + ' with AMI id ' + new_ami)

    return

def update_ami_tags(old_instance_amis=False):
    for ami in old_instance_amis:
        ami.remove_tag('current','True')
        ami.add_tag('current','False')

    return


if __name__ == '__main__':
    deploy()