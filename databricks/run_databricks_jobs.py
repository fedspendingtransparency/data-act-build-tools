import sys
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json

# TODO implement argparse

INSTANCE_ID = sys.argv[1]
JOB_NAME = sys.argv[2]
JOB_PARAMETERS = sys.argv[3]
API_VERSION = "/api/2.1"
try:
    WAIT_BOOLEAN = sys.argv[4]
except:
    print("Exception caught, boolean not set")

try:
    DEBUG = sys.argv[5]
except:
    DEBUG = "False"

DEBUG = DEBUG.lower() == "true"
WAIT_BOOLEAN = WAIT_BOOLEAN.lower() == "true" 

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

# Start a job run
def postRequest(api_command, params):
    url = "https://{}{}{}".format(INSTANCE_ID, API_VERSION, api_command)
    response = requests.post(
      url = url,
      json = params,
    )
    return response

# Get all job names and jobID"s and map to dict
def getJobIds(res):
    tempDict = {}
    for job in res.json()["jobs"]:
      tempDict[job["settings"]["name"]] = job["job_id"]
    return tempDict


if __name__ == '__main__':
    if (DEBUG):
        print("----------RUNNING JOB " + JOB_NAME )

    jobs = getJobIds(getRequest("/jobs/list"))

    if( JOB_NAME in jobs ):
        if(DEBUG):
            print("JOB ID: " + str(jobs[JOB_NAME]))

        # Set python params for job
        python_params = JOB_PARAMETERS.split(" ")

        # Used for notebook params
        # notebook_object = {}
        # for p in notebook_params:
        #     key = p.split(":")[0]
        #     paramValue = p.split(":")[1]
        #     notebook_object[key] = paramValue

        # Run Job
        job_params = { "job_id": jobs[JOB_NAME], "python_params": python_params }
        startJob = postRequest("/jobs/run-now", job_params)

        # Get run details
        run_id = startJob.json()["run_id"]
        run_params = { "run_id" : run_id }
        job_status = getRequest("/jobs/runs/get", run_params).json()["state"]["life_cycle_state"]
        if WAIT_BOOLEAN:
            # Wait for job to finish running
            while(job_status == "RUNNING" or job_status == "PENDING"):
                job_status = getRequest("/jobs/runs/get", run_params).json()["state"]["life_cycle_state"]

            # Error out if the job has not succeeded
            job_status_done = getRequest("/jobs/runs/get", run_params).json()
            if(job_status_done["state"]["result_state"] != "SUCCESS"):
                raise Exception("Job did not succeed - url: https://" + INSTANCE_ID + job_status_done["run_page_url"]) 

            tasks = getRequest("/jobs/runs/get", run_params).json()["tasks"]

            # Get all run ids for each task in the job
            all_run_ids = []
            for x in tasks:
                all_run_ids.append(x["run_id"])

            for run in all_run_ids:
                run_params = {"run_id" : run}
                finishedJob = getRequest("/jobs/runs/get-output", run_params)
                if(DEBUG):
                    print(json.dumps(json.loads(finishedJob.text), indent = 2))
                    run_url = finishedJob.json()["metadata"]["run_page_url"].replace("webapp", INSTANCE_ID+"/")
                    print("---------------SEE JOB RUN HERE: " + "https://" + run_url)
        else:
            job_status_done = getRequest("/jobs/runs/get", run_params).json()
            if not DEBUG:
                jobJson = json.loads(startJob.text)
                jobJson["url"] = job_status_done["run_page_url"].replace("webapp", INSTANCE_ID+"/")
                print(json.dumps(jobJson, indent = 2))
        
    else:
        raise ValueError(sys.argv[2] + " is not a job in databricks")
