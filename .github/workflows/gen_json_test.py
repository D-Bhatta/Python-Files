"""Generate json for md report.

This python script is used to generate the json for the
markdown report generated in the workflow jobs.
"""

import json
import os

metrics = {}

metrics["name"] = "Test with pytest, mypy, bandit, flake8, and pydocstyle"

env_info = {}

try:
    env_info["cache_hit"] = os.environ["cache_hit"]
    if env_info["cache_hit"] == "true":
        env_info["cache_hit"] = True
    elif env_info["cache_hit"] == "false":
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

test_mypy = {}

try:
    test_mypy["start_mypy"] = os.environ["start_mypy"]
except KeyError:
    test_mypy["start_mypy"] = None

try:
    test_mypy["stop_mypy"] = os.environ["stop_mypy"]
except KeyError:
    test_mypy["stop_mypy"] = None

metrics["mypy"] = test_mypy

test_bandit = {}

try:
    test_bandit["start_bandit"] = os.environ["start_bandit"]
except KeyError:
    test_bandit["start_bandit"] = None

try:
    test_bandit["stop_bandit"] = os.environ["stop_bandit"]
except KeyError:
    test_bandit["stop_bandit"] = None

metrics["bandit"] = test_bandit

test_flake8 = {}

try:
    test_flake8["start_flake8"] = os.environ["start_flake8"]
except KeyError:
    test_flake8["start_flake8"] = None

try:
    test_flake8["stop_flake8"] = os.environ["stop_flake8"]
except KeyError:
    test_flake8["stop_flake8"] = None

metrics["flake8"] = test_flake8

test_pydocstyle = {}

try:
    test_pydocstyle["start_pydocstyle"] = os.environ["start_pydocstyle"]
except KeyError:
    test_pydocstyle["start_pydocstyle"] = None

try:
    test_pydocstyle["stop_pydocstyle"] = os.environ["stop_pydocstyle"]
except KeyError:
    test_pydocstyle["stop_pydocstyle"] = None

metrics["pydocstyle"] = test_pydocstyle

metrics["env_info"] = env_info

with open("gen_json_test.json", "w", encoding="utf-8") as fio:
    json.dump(metrics, fp=fio, ensure_ascii=False, indent=4)

print(json.dumps(metrics, ensure_ascii=False, indent=4))
