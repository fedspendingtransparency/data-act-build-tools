import sys
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
from run_databricks_jobs import getJobIds, getRequest


INSTANCE_ID = sys.argv[1]
JOB_NAME = sys.argv[2]
BRANCH = sys.argv[3]
JOB_PARAMETERS = sys.argv[4]
NODE_TYPE = sys.argv[5]
WORKERS = sys.argv[6]
ENV = sys.argv[7]
FILE_LOCATION = sys.argv[8]


def updateJsonFile(fileName):
    # Open the JSON file for reading
    jsonFile = open(fileName, "r") 
    data = json.load(jsonFile) 
    jsonFile.close()

    # Edit content
    # Set notebook params for job
    python_params = JOB_PARAMETERS.split("\n")
    env_vars = {
        "DATABASE_URL": "{{secrets/" + ENV + "/DATABASE_URL}}",
        "BRANCH": BRANCH,
        "ENV_CODE": ENV 
    }

    # If we wanted to add the ability to add more tasks, we would just require a
    # loop right below here adding to data["tasks"][x]

    data["tasks"][0]["spark_python_task"]["python_file"] = "dbfs:/FileStore/" + BRANCH + "/manage.py"
    data["tasks"][0]["spark_python_task"]["parameters"] = python_params
    data["tasks"][0]["new_cluster"]["spark_env_vars"] = env_vars
    # data["tasks"][0]["new_cluster"]["node_type_id"] = "m5a.large" if data["tasks"][0]["new_cluster"]["node_type_id"] == "" else NODE_TYPE
    # data["tasks"][0]["new_cluster"]["driver_node_type_id"] = "m5a.large" if data["tasks"][0]["new_cluster"]["driver_node_type_id"] == "" else NODE_TYPE
    # data["tasks"][0]["new_cluster"]["num_workers"] = 0 if data["tasks"][0]["new_cluster"]["num_workers"] == "" else WORKERS
    data["name"] = JOB_NAME

    ## Save our changes to JSON file
    jsonFile = open(fileName, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()


if __name__ == '__main__':
    # Start script
    jobs = getJobIds(getRequest("/jobs/list"))

    if( JOB_NAME in jobs ):
        sys.stdout.write( (str(jobs[JOB_NAME])) )
        updateJsonFile(FILE_LOCATION)

    else:
        updateJsonFile(FILE_LOCATION)




