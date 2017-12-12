import boto
from boto import ec2
import sh
import os
import json
import argparse
import sys
from subprocess import Popen, PIPE, STDOUT, call

def deploy():

    packer_file     = 'usaspending-bulk-download-packer.json'
    tfvar_file      = 'usaspending-bulk-download-vars.tf.json'

    tf_file =         'usaspending-bulk-download-deploy.tf'

    packer_exec_path = '/packer/packerio'
    tf_exec_path     = '/terraform/terraform'

    # Set connection
    print('Connecting to AWS via region us-gov-west-1...')
    conn = boto.ec2.connect_to_region(region_name='us-gov-west-1')
    print('Done.')

    parser = argparse.ArgumentParser()

    parser.add_argument("--staging", 
        action="store_true", 
        help="Runs deploy for staging")
    parser.add_argument("--prod", 
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

  ###########################
  #      Packer Build       #
  ###########################

    if optionsDict["staging"]:
        deploy_env = 'staging'

    # # Get Base AMI, Update Packer file
    #     print('Retrieving base AMI...')
    #     base_ami = conn.get_all_images(filters={
    #         "tag:current" : "True", 
    #         "tag:base"    : "True", 
    #         "tag:type"    : "USASpending-API"
    #         })[0].id
    #     print('Done. Updating Packer file to pull from base AMI: ' + base_ami + '...')
    #     update_packer_spec(packer_file, base_ami)
    #     print('Done.')

    # # Get Old AMIs, for setting current=False after new one is craeted
    #     old_instance_amis = conn.get_all_images(filters={ 
    #         "tag:current" : "True", 
    #         "tag:base"    : "False", 
    #         "tag:type"    : "USASpending-API", 
    #         "tag:environment" : "staging"
    #         })

    # # Build New AMI
    #     print('**************************************************************************')
    #     print(' Building new AMI via Packer. This can take a while...')
    #     packer_output = packer_build(packer_file, packer_exec_path)
    #     ami_line = [line for line in packer_output.split('\n') if "amazon-ebs: AMIs were created:" in line][0]
    #     new_instance_ami = ami_line[ami_line.find('ami-'):ami_line.find('ami-')+12]
    #     print('Done. New AMI created: ' + new_instance_ami)


    # # Set current=False tag for old AMI
    #     print('Done. Setting current tag to False on old instance AMIs: \n' + '\n'.join(map(str, old_instance_amis)) )
    #     update_ami_tags(old_instance_amis)
    #     print('Done.')
        staging_ami = conn.get_all_images(filters={
            "tag:current"     : "True", 
            "tag:base"        : "False", 
            "tag:type"        : "USASpending-API", 
            "tag:environment" : "staging"
            })[0].id

  ###########################
  #   TF Build - Staging    #
  ###########################    

        # Add new AMI to Terraform variables
        update_tf_ami(staging_ami, tfvar_file)

        # Update Terraform User Data
        update_terraform_user_data('staging')    

        # Run Terraform
        run_tf(tf_exec_path)

  ###########################
  #   TF Build - Prod       #
  ###########################        

    elif optionsDict["prod"]:
        deploy_env = 'prod'

        # Get current Staging AMI
        staging_ami = conn.get_all_images(filters={
            "tag:current"     : "True", 
            "tag:base"        : "False", 
            "tag:type"        : "USASpending-API", 
            "tag:environment" : "staging"
            })[0].id

        # Add new AMI to Terraform variables
        update_tf_ami(staging_ami, tfvar_file)

        # Update Terraform User Data
        update_terraform_user_data('prod')  

        # Run Terraform
        run_tf(tf_exec_path)

###############################################################################
# Helper Functions
###############################################################################

def run_tf(tf_exec_path):
    # Run Terraform
    real_time_command([tf_exec_path, 'plan'])
    real_time_command([tf_exec_path, 'apply'])
    return


def packer_build(packer_file='packer.json', packer_exec_path='packer'):
    return real_time_command([packer_exec_path, 'build', packer_file, '-machine-readable'])


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
    return total_output


def update_packer_spec(packer_file='packer.json', base_ami=''):
    packer_json = open(packer_file, "r")
    packer_data = json.load(packer_json)
    packer_json.close()

    packer_data['builders'][0]['source_ami'] = base_ami

    packer_json = open(packer_file, "w+")
    packer_json.write(json.dumps(packer_data))
    packer_json.close()

    return


def update_tf_ami(new_ami='', tfvar_file='variables.tf.json'):
    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()

    tfvar_data['variable']['aws_amis']['default']['us-gov-west-1'] = new_ami

    tfvar_json = open(tfvar_file, "w+")
    tfvar_json.write(json.dumps(tfvar_data))
    tfvar_json.close()

    print ('Updated ' + tfvar_file + ' with AMI id ' + new_ami)

    return


def update_terraform_user_data(environment='staging', tf_file='usaspending-bulk-download-deploy.tf'):
    f = open(tf_file,'r')
    filedata = f.read()
    f.close()

    if environment == 'prod':
        newdata = filedata.replace("usaspending-start-staging.sh","usaspending-start-prod.sh")
    elif environment == 'staging':
        newdata = filedata.replace("usaspending-start-prod.sh","usaspending-start-staging.sh")

    f = open(tf_file,'w')
    f.write(newdata)
    f.close()

    print ('Updated ' + tf_file + ' with user data script for ' + environment)

    return


def update_ami_tags(old_instance_amis=False):
    for ami in old_instance_amis:
        ami.remove_tag('current','True')
        ami.add_tag('current','False')
    return


if __name__ == '__main__':
    deploy()
