import boto
from boto import ec2
import sh
import os
import json
import argparse
import sys
from subprocess import Popen, PIPE, STDOUT, call

EXIT_CODE = 0

def deploy():

    # This tf_var file is expected to be copied from an external source
    tfvar_file       = 'usaspending-vars.tf.json'

    tf_exec_path     = '/terraform/terraform'
    tf_file          = 'usaspending-deploy.tf'

    packer_exec_path = '/packer/packerio'
    packer_file      = 'usaspending-packer.json'
    
    # Set connection
    print('Connecting to AWS via region us-gov-west-1...')
    conn = boto.ec2.connect_to_region(region_name='us-gov-west-1')
    print('Done.')

    parser = argparse.ArgumentParser()

    parser.add_argument("--sandbox", 
        action="store_true", 
        help="Runs deploy for sandbox")
    parser.add_argument("--dev", 
        action="store_true", 
        help="Runs deploy for dev")
    parser.add_argument("--staging", 
        action="store_true", 
        help="Runs deploy for staging")
    parser.add_argument("--prod-safe", 
        action="store_true", 
        help="Redeploy to prod")
    parser.add_argument("--prod-push", 
        action="store_true", 
        help="Tag current staging AMI and deploy it to production")
    args = parser.parse_args()
    optionsDict = vars(args)
    noArgs = True

    for arg in optionsDict:
        if(optionsDict[arg]):
            noArgs = False

    if noArgs:
        print ("No environment specified. Please include an argument: --sandbox, --dev, --staging, or --prod")
        sys.exit(1)

  ###########################
  #      Packer Build       #
  ###########################

  # Sandbox, dev, and staging are all built the same way: packer, then create TF resources
  # Prod pulls the same staging AMI that packer creates, and alters the launch config/AWS names

    if optionsDict["sandbox"]:
        deploy_env = 'sandbox'

    if optionsDict["dev"]:
        deploy_env = 'dev'

    if optionsDict["staging"]:
        deploy_env = 'staging'

    if optionsDict["sandbox"] or optionsDict["dev"] or optionsDict["staging"]:

        # Get Base AMI, Update Packer file
        print('Retrieving base AMI...')
        base_ami = conn.get_all_images(filters={
            "tag:current" : "True", 
            "tag:base"    : "True", 
            "tag:type"    : "USASpending-API"
            })[0].id
        print('Done. Updating Packer file to pull from base AMI: ' + base_ami + '...')
        update_packer_spec(packer_file, base_ami, deploy_env)
        print('Done.')

        # Get Old AMIs, for setting current=False after new one is created
        old_instance_amis = conn.get_all_images(filters={ 
            "tag:current" : "True", 
            "tag:base"    : "False", 
            "tag:type"    : "USASpending-API", 
            "tag:environment" : deploy_env
            })

        # Build New AMI (Packer)
        print('**************************************************************************')
        print(' Building new AMI via Packer. This can take a while...')
        packer_output = real_time_command([packer_exec_path, 'build', packer_file, '-machine-readable'])
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
        update_tf_ami(new_instance_ami, tfvar_file)

        # Update Terraform User Data
        update_terraform_user_data(deploy_env)    

        # Run Terraform plan and apply
        real_time_command([tf_exec_path, 'plan'])
        real_time_command([tf_exec_path, 'apply'])

  ###########################
  #   TF Build - Prod       #
  ###########################        

    elif optionsDict["prod-push"] or optionsDict["prod-safe"]:

        if optionsDict["prod-push"]:

            # Un-tag current-prod AMIs
            old_prod = conn.get_all_images(filters={
                "tag:type"         : "USASpending-API", 
                "tag:current-prod" : "True"
                })

            for ami in old_prod:
                print('Setting "current-prod" tag to False for AMI {}...'.format(ami.id))
                ami.remove_tag('current-prod','True')
                ami.add_tag('current-prod','False')

            # Get current Staging AMI
            staging_ami = conn.get_all_images(filters={
                "tag:current"     : "True", 
                "tag:base"        : "False", 
                "tag:type"        : "USASpending-API", 
                "tag:environment" : "staging"
                })[0]

            # Tag current Staging AMI for prod deployments
            print('Setting "current-prod" tag to True for AMI {}...'.format(staging_ami.id))
            staging_ami.add_tag('current-prod','True')

        # Get current Production AMI
        prod_ami = conn.get_all_images(filters={
            "tag:type"         : "USASpending-API", 
            "tag:current-prod" : "True"
            })[0].id

        # Add new AMI to Terraform variables
        update_tf_ami(prod_ami, tfvar_file)

        # Update Terraform User Data
        update_terraform_user_data('prod')  

        # Run Terraform plan and apply
        real_time_command([tf_exec_path, 'plan'])
        real_time_command([tf_exec_path, 'apply'])

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


def update_packer_spec(packer_file='packer.json', base_ami='', environment='staging'):
    packer_json = open(packer_file, "r")
    packer_data = json.load(packer_json)
    packer_json.close()

    packer_data['builders'][0]['source_ami'] = base_ami

    if environment == 'dev' or environment == 'sandbox':
        packer_data['builders'][0]['tags']['environment'] = environment
        packer_data['provisioners'][0]['extra_arguments'] = "--extra-vars 'BRANCH={} HOST=local'".format(environment)

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


def update_ami_tags(old_instance_amis=False):
    for ami in old_instance_amis:
        ami.remove_tag('current','True')
        ami.add_tag('current','False')
    return


if __name__ == '__main__':
    deploy()
