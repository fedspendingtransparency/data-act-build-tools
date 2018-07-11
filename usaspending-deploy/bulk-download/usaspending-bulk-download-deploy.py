import boto
from boto import ec2
import json
import argparse
import sys
from subprocess import Popen, PIPE

EXIT_CODE = 0

def deploy():

    # This tf_var file is expected to be copied from an external source
    tfvar_file   = 'usaspending-bulk-download-vars.tf.json'

    tf_exec_path = '/opt/terraform/terraform'
    tf_file      = 'usaspending-deploy.tf'

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
        print ("No environment specified. Please include an argument: --sandbox, --dev, --staging, or --prod")
        sys.exit(1)

    if optionsDict["sandbox"]:
        deploy_env = 'sandbox'

    if optionsDict["dev"]:
        deploy_env = 'dev'

    if optionsDict["staging"] or optionsDict["prod"]: # both pull staging AMI
        deploy_env = 'staging'

    # Get previously created API AMI (created by usaspending-deploy.py)
    current_api_ami = conn.get_all_images(filters={
        "tag:current": "True",
        "tag:base": "False",
        "tag:type": "USASpending-API",
        "tag:environment": deploy_env
    })[0].id

    # Add API AMI to Terraform variables
    update_tf_ami(current_api_ami, tfvar_file)

    # Run Terraform plan and apply
    real_time_command([tf_exec_path, 'plan', "--input=false"])
    real_time_command([tf_exec_path, 'apply', "--input=false", "--auto-approve"])

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
    tfvar_json.write(json.dumps(tfvar_data))
    tfvar_json.close()

    print ('Updated ' + tfvar_file + ' with AMI id ' + new_ami)

    return


if __name__ == '__main__':
    deploy()
