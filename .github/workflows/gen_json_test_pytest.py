"""Generate json for md report.

This python script is used to generate the json for the
markdown report generated in the workflow jobs.
"""

import json
import os

metrics = {}

metrics["name"] = "Test with pytest"
metrics["id"] = "test-pytest"

env_info = {}

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

test_pytest = {}

try:
    test_pytest["start_pytest"] = os.environ["start_pytest"]
except KeyError:
    test_pytest["start_pytest"] = None

try:
    test_pytest["stop_pytest"] = os.environ["stop_pytest"]
except KeyError:
    test_pytest["stop_pytest"] = None

metrics["pytest"] = test_pytest

metrics["env_info"] = env_info

with open("gen_json_test_pytest.json", "w", encoding="utf-8") as fio:
    json.dump(metrics, fp=fio, ensure_ascii=False, indent=4)

print(json.dumps(metrics, ensure_ascii=False, indent=4))
