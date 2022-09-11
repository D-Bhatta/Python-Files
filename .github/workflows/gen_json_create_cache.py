"""Generate json for md report.

This python script is used to generate the json for the
markdown report generated in the ``create-cache`` workflow job.
"""

import json
import os

metrics = {}

metrics["name"] = "Create python cache if not present"

try:
    metrics["job-id"] = os.environ["GITHUB_JOB"]
except KeyError:
    metrics["job-id"] = "ERROR: GITHUB_JOB env variable is missing"

env_info = {}

try:
    env_info["CI"] = os.environ["CI"]
except KeyError:
    env_info["CI"] = "ERROR: CI env variable is missing"

try:
    env_info["CI_TEST_ENV"] = os.environ["CI_TEST_ENV"]
except KeyError:
    env_info["CI_TEST_ENV"] = "ERROR: CI_TEST_ENV env variable is missing"

try:
    env_info["cache_hit"] = os.environ["cache_hit"]
    if env_info["cache_hit"] == "true":
        env_info["cache_hit"] = True
    elif env_info["cache_hit"] == "false" or env_info["cache_hit"] == "":
        env_info["cache_hit"] = False
    else:
        unknown_cache_hit_val = os.environ.get("cache_hit")
        raise ValueError(f"Unknown value for key 'cache_hit':{unknown_cache_hit_val}")
except KeyError:
    env_info["cache_hit"] = None

if not env_info["cache_hit"]:
    # Cache didn't hit, venv was created, or something went wrong
    create_venv = {}
    try:
        create_venv["start_create_venv"] = os.environ["start_create_venv"]
    except KeyError:
        create_venv["start_create_venv"] = None

    try:
        create_venv["stop_create_venv"] = os.environ["stop_create_venv"]
    except KeyError:
        create_venv["stop_create_venv"] = None

    env_info["create_venv"] = create_venv

try:
    env_info["python_ver"] = os.environ["python_ver"]
except KeyError:
    env_info["python_ver"] = None

try:
    env_info["pip_ver"] = os.environ["pip_ver"]
except KeyError:
    env_info["pip_ver"] = None

try:
    env_info["pip_freeze"] = os.environ["pip_freeze"]
except KeyError:
    env_info["pip_freeze"] = None

metrics["env_info"] = env_info

with open("gen_json_create_cache.json", "w", encoding="utf-8") as fio:
    json.dump(metrics, fp=fio, ensure_ascii=False, indent=4)

print(json.dumps(metrics, ensure_ascii=False, indent=4))
