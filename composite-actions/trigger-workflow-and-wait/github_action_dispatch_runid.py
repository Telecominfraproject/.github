import random
import os
import string
import datetime
import requests
import time

# Get required env variable values
owner = os.environ.get('OWNER') 
repo = os.environ.get('REPO')
workflow = os.environ.get('WORKFLOW')
token = os.environ.get('TOKEN')
ref = os.environ.get('REF')
owgw_version = os.environ.get('OWGW_VERSION')
owgwui_version = os.environ.get('OWGWUI_VERSION')
owsec_version = os.environ.get('OWSEC_VERSION')
owfms_version = os.environ.get('OWFMS_VERSION')
owprov_version = os.environ.get('OWPROV_VERSION')
owprovui_version = os.environ.get('OWPROVUI_VERSION')

authHeader = { "Authorization": f"Token {token}" }

# generate a random id
run_identifier = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
# filter runs that were created after this date minus 5 minutes
delta_time = datetime.timedelta(minutes=5)
run_date_filter = (datetime.datetime.utcnow()-delta_time).strftime("%Y-%m-%dT%H:%M") 

r = requests.post(f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches",
    headers= authHeader,
    json= {
        "ref": ref,
        "inputs":{ 
            "id": run_identifier,
            "owgw_version": owgw_version,
            "owgwui_version": owgwui_version,
            "owsec_version": owsec_version,
            "owfms_version": owfms_version,
            "owprov_version": owprov_version,
            "owprovui_version": owprovui_version,
        }
    })

print(f"dispatch workflow status: {r.status_code} | workflow identifier: {run_identifier}")
workflow_id = ""

while workflow_id == "":
        
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/actions/runs?created=%3E{run_date_filter}",
        headers = authHeader)
    runs = r.json()["workflow_runs"]

    if len(runs) > 0:
        for workflow in runs:
            jobs_url = workflow["jobs_url"]
            print(f"get jobs_url {jobs_url}")

            r = requests.get(jobs_url, headers= authHeader)
            
            jobs = r.json()["jobs"]
            if len(jobs) > 0:
                # we only take the first job, edit this if you need multiple jobs
                job = jobs[0]
                steps = job["steps"]
                if len(steps) >= 2:
                    second_step = steps[1] # if you have position the run_identifier step at 1st position
                    if second_step["name"] == run_identifier:
                        workflow_id = job["run_id"]
                else:
                    print("waiting for steps to be executed...")
                    time.sleep(3)
            else:
                print("waiting for jobs to popup...")
                time.sleep(3)
    else:
        print("waiting for workflows to popup...")
        time.sleep(3)

print(f"workflow_id: {workflow_id}")
