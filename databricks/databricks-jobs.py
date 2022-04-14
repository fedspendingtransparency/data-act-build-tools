import sys
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json

# REMOVE WHEN SSL IS ENABLED
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

INSTANCE_ID = sys.argv[1]
JOB_NAME = sys.argv[2]
API_VERSION = '/api/2.1'

print("----------RUNNING JOB " + JOB_NAME )

# Run Get request with api_command param
# /jobs/list/ with api 2.0 returns all jobs, 2.1 does not
def getRequest(api_command, params={}):
    if api_command == '/jobs/list':
        url = "https://{}{}{}".format(INSTANCE_ID, '/api/2.0', api_command)
    else:
        url = "https://{}{}{}".format(INSTANCE_ID, API_VERSION, api_command)
    response = requests.get(
      url = url,
      json = params,
      verify = False #Needed because we dont have ssl
    )
    return response

# Start a job run
def postRequest(api_command, params):
    url = "https://{}{}{}".format(INSTANCE_ID, API_VERSION, api_command)
    response = requests.post(
      url = url,
      json = params,
      verify = False #Needed because we dont have ssl
    )
    return response

# Get all job names and jobID's and map to dict
def getJobIds(res):
    tempDict = {}
    for job in res.json()['jobs']:
      tempDict[job['settings']['name']] = job['job_id']
    return tempDict

jobs = getJobIds(getRequest('/jobs/list'))

if( JOB_NAME in jobs ):
    print("JOB ID: " + str(jobs[JOB_NAME]))

    job_params = {'job_id': jobs[JOB_NAME]}
    startJob = postRequest('/jobs/run-now', job_params)

    run_id = startJob.json()['run_id']
    run_params = { 'run_id' : run_id }
    job_status = getRequest('/jobs/runs/get-output', run_params).json()["metadata"]["state"]["life_cycle_state"]

    #Wait for job to finish running
    while(job_status == "RUNNING" or job_status == "PENDING"):
        job_status = getRequest('/jobs/runs/get-output', run_params).json()["metadata"]["state"]["life_cycle_state"]

    finishedJob = getRequest('/jobs/runs/get-output', run_params)
    print(json.dumps(json.loads(finishedJob.text), indent = 2))

    run_url = finishedJob.json()["metadata"]["run_page_url"].replace("webapp", INSTANCE_ID+"/")
    print("---------------SEE JOB RUN HERE: " + run_url)
else:
    raise ValueError(sys.argv[2] + " is not a job in databricks")
