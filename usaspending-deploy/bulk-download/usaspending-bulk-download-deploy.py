import boto
from boto import ec2
import json
import argparse
import sys
from subprocess import Popen, PIPE


def deploy():

    # This file gets copied over from either prod-bulk-download-vars.tf.json or staging-bulk-download-vars.tf.json
    tfvar_file = 'usaspending-bulk-download-vars.tf.json'
    tf_exec_path = '/terraform/terraform'

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

    # TODO Can add arguments with this and combine with create-and-start-csv.py
    if noArgs:
        print ("No environment specified. Please include an argument: --staging, or --prod")
        sys.exit(1)

    # Get previously created staging AMI (created by usaspending-deploy.py)
    staging_ami = conn.get_all_images(filters={
        "tag:current": "True",
        "tag:base": "False",
        "tag:type": "USASpending-API",
        "tag:environment": "staging"
    })[0].id

    # Staging and prod do the same thing with different tfvar_files
    if optionsDict["staging"] or optionsDict["prod"]:
        # Add new AMI to Terraform variables
        update_tf_ami(staging_ami, tfvar_file)

        # Run Terraform
        run_tf(tf_exec_path)

###############################################################################
# Helper Functions
###############################################################################


def run_tf(tf_exec_path):
    real_time_command([tf_exec_path, 'plan'])
    real_time_command([tf_exec_path, 'apply'])
    return


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
