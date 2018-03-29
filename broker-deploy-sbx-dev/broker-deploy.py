import boto
from boto import ec2
import sh
import os
import json
import argparse
import sys
from subprocess import Popen, PIPE, STDOUT, call

EXIT_CODE = 0
# set global boto connection
conn = boto.ec2.connect_to_region(region_name='us-gov-west-1')

def deploy():

    # set paths
    packer_file = 'broker-packer.json'
    tfvar_file = 'broker-vars.tf.json'
    packer_exec_path = '/packer/packerio'
    tf_exec_path = '/terraform/terraform'

    parser = argparse.ArgumentParser()

    parser.add_argument("-sbx", "--sandbox", action="store_true", help="Runs deploy for sandbox")
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
        print ("No environment specified. Please include an argument: --sandbox, --dev, --staging, --prod")
        sys.exit(1)

    if optionsDict["sandbox"]:
        deploy_env = 'sandbox'

    if optionsDict["dev"]:
        deploy_env = 'dev'

    if optionsDict["staging"]:
        deploy_env = 'staging'

    if optionsDict["prod"]:
        deploy_env = 'prod'

    tfvar_file = deploy_env + '-variables.tf.json'
    packer_file = deploy_env + '-packer.json'

    if optionsDict["sandbox"]:
        current_base_ami = get_current_base_ami()
        update_lc_ami(current_base_ami, tfvar_file, 'sbx')

        ## Possible to-do: only run terraform when active instances are not running on current base ami
        # val_instance = get_running_instance(deploy_env='sbx', component='Validator')
        # api_instance = get_running_instance(deploy_env='sbx', component='API')
        # if val_instance.image_id != api_instance.image_id:
        #     print("Error, current environment not configured correctly.")
        #     EXIT_CODE = 1
        #     sys.exit(EXIT_CODE)
        # elif val_instance.image_id != current_base_ami: # temporarily forcing false to test
        #     # Create hosts file for ansible and exit with 0 code
        #     with open('hosts','w') as f:
        #         f.write('[validator]\n')
        #         f.write(val_instance.private_ip_address + '\n')
        #         f.write('\n')
        #         f.write('[api]\n')
        #         f.write(api_instance.private_ip_address + '\n')
        #     print("Current base AMI in use. Hosts file has been built for deploying via ansible.")
        #     EXIT_CODE = 0
        #     sys.exit(EXIT_CODE)

        # else:
        #     # Run terraform
        #     update_lc_ami(current_base_ami, 'temp.tf.json', 'sbx')

        #Run terraform

        real_time_command([tf_exec_path, 'plan'])
        real_time_command([tf_exec_path, 'apply'])

    elif optionsDict["dev"] or optionsDict["staging"]:

        # Retrieve current Base app AMI (where type=app and current=true)
        print('Retrieving current base app AMI...')

        current_base_ami = get_current_base_ami()

        # Insert current Base app AMI into packer file
        print('Updating Packer file with current base app AMI ' + current_base_ami + '...')
        update_packer_spec(packer_file, current_base_ami)
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
        if ami_id == conn.get_all_images(filters={
            "tag:current" : "True",
            "tag:base" : "False",
            "tag:type" : "Application",
            "tag:environment" : deploy_env
            })[0].id:
            print('Success! Packer AMI id matches current tagged AMI.')
        else:
            print('Something went wrong. Packer AMI: '+ami_id+'; Tagged AMI: '+conn.get_all_images(filters={"tag:current" : "True", "tag:base" : "False", "tag:type" : "Application", "tag:environment" : deploy_env})[0].id)

        #Add new AMI id to terraform variables
        update_lc_ami(ami_id, tfvar_file, deploy_env)

        #Run terraform
        real_time_command([tf_exec_path, 'plan'])
        real_time_command([tf_exec_path, 'apply'])

    elif optionsDict["prod"]:
        #For prod, we don't build a new artifact, we just run terraform against the current staging AMI
        deploy_env = 'prod'
        # get current staging AMI
        staging_ami = conn.get_all_images(filters={"tag:current" : "True", "tag:base" : "False", "tag:type" : "Application", "tag:environment" : "staging"})[0].id
        # Update terraform variables with staging ami_id
        update_lc_ami(staging_ami, tfvar_file, deploy_env)
        print(staging_ami)
        #Run terraform
        real_time_command([tf_exec_path, 'plan'])
        real_time_command([tf_exec_path, 'apply'])

    global EXIT_CODE
    if EXIT_CODE != 0:
        print('Exiting with a code of {}'.format(EXIT_CODE))
        sys.exit(EXIT_CODE)

def get_running_instance(deploy_env='sbx', component='Validator'):
    reservations = conn.get_all_instances(filters={
        "tag:Application" : "Broker",
        "tag:Component" : component,
        "tag:Environment" : deploy_env
        })
    if len(reservations) != 1:
        print("Error, current environment not configured correctly.")
        EXIT_CODE = 1
        return
    else:
        return reservations[0].instances[0]

def get_current_base_ami():
    base_ami = conn.get_all_images(filters={
        "tag:current" : "True",
        "tag:base" : "True",
        "tag:type" : "Application"
        })[0].id

    return base_ami

def get_current_app_instance_amis(deploy_env):
    app_instance_amis = conn.get_all_images(filters={
        "tag:current" : "True",
        "tag:base" : "False",
        "tag:type" : "Application",
        "tag:environment" : deploy_env
        })
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

def update_packer_spec(packer_file='packer.json', current_base_ami=''):
    packer_json = open(packer_file, "r")
    packer_data = json.load(packer_json)
    packer_json.close()

    packer_data['builders'][0]['source_ami'] = current_base_ami

    packer_json = open(packer_file, "w+")
    packer_json.write(json.dumps(packer_data))
    packer_json.close()

    return

def update_lc_ami(new_ami='', tfvar_file='variables.tf.json', deploy_env='sbx'):
    tfvar_json = open(tfvar_file, "r")
    tfvar_data = json.load(tfvar_json)
    tfvar_json.close()
    if deploy_env == 'sbx':
        tfvar_data['variable']['base_ami']['default'] = new_ami
    else:
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

#================================ EOF ==========================================#
