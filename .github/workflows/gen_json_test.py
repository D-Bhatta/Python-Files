"""Generate json for md report.

This python script is used to generate the json for the
markdown report generated in the workflow jobs.
"""

import json
import os

metrics = {}

metrics["name"] = "Test with pytest"

try:
    metrics["test_cache_hit"] = os.environ["test_cache_hit"]
except KeyError:
    metrics["test_cache_hit"] = None

try:
    metrics["start_test_create_environment"] = os.environ[
        "start_test_create_environment"
    ]
except KeyError:
    metrics["start_test_create_environment"] = None

try:
    metrics["stop_test_create_environment"] = os.environ["stop_test_create_environment"]
except KeyError:
    metrics["stop_test_create_environment"] = None

try:
    metrics["check_formatting_env_info"] = os.environ["check_formatting_env_info"]
except KeyError:
    metrics["check_formatting_env_info"] = None

try:
    metrics["start_test_test_pytest"] = os.environ["start_test_test_pytest"]
except KeyError:
    metrics["start_test_test_pytest"] = None

try:
    metrics["stop_test_test_pytest"] = os.environ["stop_test_test_pytest"]
except KeyError:
    metrics["stop_test_test_pytest"] = None

with open("gen_json_test.json", "w", encoding="utf-8") as fio:
    json.dump(metrics, fp=fio, ensure_ascii=False, indent=4)

print(json.dumps(metrics, ensure_ascii=False, indent=4))
