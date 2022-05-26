"""Generate json for md report.

This python script is used to generate the json for the
markdown report generated in the workflow jobs.
"""

import json
import os

metrics = {}

metrics["name"] = "Check code formatting with black"

try:
    metrics["check_fmt_cache_hit"] = os.environ["check_fmt_cache_hit"]
    if metrics["check_fmt_cache_hit"] == "true":
        metrics["check_fmt_cache_hit"] = True
    elif metrics["check_fmt_cache_hit"] == "false":
        metrics["check_fmt_cache_hit"] = False
    else:
        raise ValueError("Unknown value for key 'check_fmt_cache_hit' in metrics.")
except KeyError:
    metrics["check_fmt_cache_hit"] = None

try:
    metrics["start_check_formatting_create_environment"] = os.environ[
        "start_check_formatting_create_environment"
    ]
except KeyError:
    metrics["start_check_formatting_create_environment"] = None

try:
    metrics["stop_check_formatting_create_environment"] = os.environ[
        "stop_check_formatting_create_environment"
    ]
except KeyError:
    metrics["stop_check_formatting_create_environment"] = None

try:
    metrics["check_formatting_env_info"] = os.environ["check_formatting_env_info"]
except KeyError:
    metrics["check_formatting_env_info"] = None

try:
    metrics["start_check_formatting_run_black"] = os.environ[
        "start_check_formatting_run_black"
    ]
except KeyError:
    metrics["start_check_formatting_run_black"] = None

try:
    metrics["stop_check_formatting_run_black"] = os.environ[
        "stop_check_formatting_run_black"
    ]
except KeyError:
    metrics["stop_check_formatting_run_black"] = None

with open("gen_json.json", "w", encoding="utf-8") as fio:
    json.dump(metrics, fp=fio, ensure_ascii=False, indent=4)

print(json.dumps(metrics, ensure_ascii=False, indent=4))
