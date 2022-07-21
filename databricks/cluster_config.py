import sys
import requests
import argparse
import json
from run_databricks_jobs import getJobIds, getRequest

# Setup args for cluster config
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--instance-id', required=True)
parser.add_argument('-j', '--job-name', default='manage', required=True)
parser.add_argument('-b', '--branch', default='qat', required=True)
parser.add_argument('-p', '--job-parameters', required=True)
parser.add_argument('-e', '--env', required=True)
parser.add_argument('-w', '--workers', default=16)
parser.add_argument('-f', '--file-location', required=True)
args = parser.parse_args()
INSTANCE_ID = args.instance_id

def updateJsonFile(fileName):
    # Open the JSON file for reading
    jsonFile = open(fileName, "r") 
    data = json.load(jsonFile) 
    jsonFile.close()

    if args.env == "staging":
        envCode = "stg"  
    else:
        envCode = args.env     

    # Edit content
    # Set python params for job
    python_params = args.job_parameters.split(" ")
    secretKey = "DATABASE_URL"
    if args.env == "qat":
        secretKey = "PERF_DATABASE_URL"
        
    env_vars = {
        "DATABASE_URL": "{{secrets/" + args.env + "/" + secretKey + "}}",
        "BRANCH": args.branch,
        "ENV_CODE": envCode
    }
    if "manage" in args.job_name:
        subnet = args.job_name.split("-")
        subnet_param = "us-gov-west-" + subnet[1]
    else:
        subnet_param = "us-gov-west-1a"

    # If we wanted to add the ability to add more tasks, we would just require a
    # loop right below here adding to data["tasks"][x]

    data["tasks"][0]["spark_python_task"]["python_file"] = "dbfs:/FileStore/" + args.branch + "/manage.py"
    data["tasks"][0]["spark_python_task"]["parameters"] = python_params
    data["tasks"][0]["new_cluster"]["spark_env_vars"] = env_vars
    data["tasks"][0]["new_cluster"]["aws_attributes"]["zone_id"] = subnet_param
    # data["tasks"][0]["new_cluster"]["node_type_id"] = "m5a.large" if data["tasks"][0]["new_cluster"]["node_type_id"] == "" else NODE_TYPE
    # data["tasks"][0]["new_cluster"]["driver_node_type_id"] = "m5a.large" if data["tasks"][0]["new_cluster"]["driver_node_type_id"] == "" else NODE_TYPE
    data["tasks"][0]["new_cluster"]["num_workers"] = args.workers
    data["name"] = args.job_name

    ## Save our changes to JSON file
    jsonFile = open(fileName, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()


if __name__ == '__main__':
    # Start script
    jobs = getJobIds(getRequest("/jobs/list"))

    if( args.job_name in jobs ):
        sys.stdout.write( (str(jobs[args.job_name])) )
        updateJsonFile(args.file_location)

    else:
        updateJsonFile(args.file_location)




