"""Generate json for md report.

This python script is used to generate the json for the
markdown report generated in the workflow jobs.
"""

import json
import os

metrics = {}

try:
    metrics["venv-cache.outputs.cache-hit"] = os.environ[
        "STEPS_VENV_CACHE_OUTPUTS_CACHE_HIT"
    ]
except KeyError:
    metrics["venv-cache.outputs.cache-hit"] = None

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

print(json.dumps(metrics, ensure_ascii=False, indent=4))
