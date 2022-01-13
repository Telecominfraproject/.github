import random
import os
import json
import sys
import argparse
import string
import datetime
import requests
import time


def trigger_workflow_and_get_id():
    # generate a random id
    run_identifier = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=15))
    # filter runs that were created after this date minus 5 minutes
    delta_time = datetime.timedelta(minutes=5)
    run_date_filter = (datetime.datetime.utcnow() -
                       delta_time).strftime("%Y-%m-%dT%H:%M")

    authHeader = {"Authorization": f"Token {args.token}"}

    id_dict = {"id": run_identifier}
    if args.inputs:
        inputs_dict = json.loads(args.inputs)
    else:
        inputs_dict = {}

    r = requests.post(
        f"https://api.github.com/repos/{args.owner}/{args.repo}/actions/workflows/{args.workflow}/dispatches",
        headers=authHeader,
        json={
            "ref": args.ref,
            "inputs": {**id_dict, **inputs_dict}
        })

    print(
        f"dispatch workflow status: {r.status_code} | workflow identifier: {run_identifier}")
    workflow_id = ""

    while workflow_id == "":

        r = requests.get(
            f"https://api.github.com/repos/{args.owner}/{args.repo}/actions/runs?created=%3E{run_date_filter}",
            headers=authHeader)
        runs = r.json()["workflow_runs"]

        if len(runs) > 0:
            for workflow in runs:
                jobs_url = workflow["jobs_url"]
                print(f"get jobs_url {jobs_url}")

                r = requests.get(jobs_url, headers=authHeader)

                jobs = r.json()["jobs"]
                if len(jobs) > 0:
                    # we only take the first job, edit this if you need multiple jobs
                    job = jobs[0]
                    steps = job["steps"]
                    if len(steps) >= 2:
                        # if you have position the run_identifier step at 1st position
                        second_step = steps[1]
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

    print(f"Successfully triggered workflow with ID {workflow_id}.")
    return workflow_id


def wait_for_workflow():
    workflow_id = trigger_workflow_and_get_id()

    status = ""

    while status != "completed":
        time.sleep(30)
        r = requests.get(
            f"https://api.github.com/repos/{args.owner}/{args.repo}/actions/runs/{workflow_id}")
        status = r.json()["status"]
        print(f"Current status of the workflow run is {status}.")

    conclusion = r.json()["conclusion"]

    if conclusion == "success":
        print(f"Workflow with ID {workflow_id} completed successfully.")
        sys.exit(0)
    else:
        print(
            f"Workflow with ID {workflow_id} failed or has been canceled, "
            "please check the logs at "
            f"https://github.com/{args.owner}/{args.repo}/actions/runs/{workflow_id}.")
        sys.exit(1)


def main():
    wait_for_workflow()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner')
    parser.add_argument('--repo')
    parser.add_argument('--workflow')
    parser.add_argument('--token')
    parser.add_argument('--ref')
    parser.add_argument('--inputs')
    args = parser.parse_args()

    main()
