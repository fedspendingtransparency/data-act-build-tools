import sys
import requests
import json
import argparse

API_VERSION = "/api/2.1"

# Run Get request with api_command param
# /jobs/list/ with api 2.0 returns all jobs, 2.1 does not
def getRequest(api_command, instance_id, params={}):
    if api_command == "/jobs/list":
        url = "https://{}{}{}".format(instance_id, "/api/2.0", api_command)
    else:
        url = "https://{}{}{}".format(instance_id, API_VERSION, api_command)
    response = requests.get(
      url = url,
      json = params,
    )
    return response

# Start a job run
def postRequest(api_command, params, instance_id):
    url = "https://{}{}{}".format(instance_id, API_VERSION, api_command)
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
    # Setup args for cluster config
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--instance-id', required=True)
    parser.add_argument('-j', '--job-name', required=True)
    parser.add_argument('-p', '--job-parameters', required=True)
    parser.add_argument('--wait', default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    INSTANCE_ID = args.instance_id
    JOB_NAME = args.job_name
    JOB_PARAMETERS = args.job_parameters

    DEBUG = args.debug
    WAIT_BOOLEAN = args.wait

    if (DEBUG):
        print("----------RUNNING JOB " + JOB_NAME )

    jobs = getJobIds(getRequest("/jobs/list", INSTANCE_ID))

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
        startJob = postRequest("/jobs/run-now", job_params, INSTANCE_ID)

        # Get run details
        run_id = startJob.json()["run_id"]
        run_params = { "run_id" : run_id }
        job_status = getRequest("/jobs/runs/get", INSTANCE_ID, run_params).json()["state"]["life_cycle_state"]
        if WAIT_BOOLEAN:
            # Wait for job to finish running
            while(job_status == "RUNNING" or job_status == "PENDING"):
                job_status = getRequest("/jobs/runs/get", INSTANCE_ID, run_params).json()["state"]["life_cycle_state"]

            # Error out if the job has not succeeded
            job_status_done = getRequest("/jobs/runs/get", INSTANCE_ID, run_params).json()
            if(job_status_done["state"]["result_state"] != "SUCCESS"):
                url = job_status_done["run_page_url"].replace("webapp", "https://" + INSTANCE_ID + "/")
                raise Exception("Job did not succeed - url: " + url) 

            tasks = getRequest("/jobs/runs/get", INSTANCE_ID, run_params).json()["tasks"]

            # Get all run ids for each task in the job
            all_run_ids = []
            for x in tasks:
                all_run_ids.append(x["run_id"])

            for run in all_run_ids:
                run_params = {"run_id" : run}
                finishedJob = getRequest("/jobs/runs/get-output", INSTANCE_ID, run_params)
                if(DEBUG):
                    print(json.dumps(json.loads(finishedJob.text), indent = 2))
                    run_url = finishedJob.json()["metadata"]["run_page_url"].replace("webapp", INSTANCE_ID+"/")
                    print("---------------SEE JOB RUN HERE: " + "https://" + run_url)
        else:
            job_status_done = getRequest("/jobs/runs/get", INSTANCE_ID, run_params).json()
            if not DEBUG:
                jobJson = json.loads(startJob.text)
                jobJson["url"] = job_status_done["run_page_url"].replace("webapp", "https://" + INSTANCE_ID + "/")
                print(json.dumps(jobJson, indent = 2))
        
    else:
        raise ValueError(sys.argv[2] + " is not a job in databricks")
