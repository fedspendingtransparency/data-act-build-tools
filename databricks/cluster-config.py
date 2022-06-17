import sys
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json


INSTANCE_ID = sys.argv[1]
JOB_NAME = sys.argv[2]
BRANCH = sys.argv[3]
JOB_PARAMETERS = sys.argv[4]
ENV = sys.argv[5]
FILE_LOCATION = sys.argv[6]

# Run Get request with api_command param
# /jobs/list/ with api 2.0 returns all jobs, 2.1 does not
def getRequest(api_command, params={}):
    if api_command == "/jobs/list":
        url = "https://{}{}{}".format(INSTANCE_ID, "/api/2.0", api_command)
    else:
        url = "https://{}{}{}".format(INSTANCE_ID, API_VERSION, api_command)
    response = requests.get(
      url = url,
      json = params,
    )
    return response


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
    data["tasks"][0]["spark_python_task"]["python_file"] = "dbfs:/FileStore/" + BRANCH + "/manage.py"
    data["tasks"][0]["spark_python_task"]["parameters"] = python_params
    data["tasks"][0]["new_cluster"]["spark_env_vars"] = env_vars

    ## Save our changes to JSON file
    jsonFile = open(fileName, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()




# Start script
jobs = getJobIds(getRequest("/jobs/list"))

if( JOB_NAME in jobs ):
    sys.stdout.write( (str(jobs[JOB_NAME])) )


    updateJsonFile(FILE_LOCATION)




