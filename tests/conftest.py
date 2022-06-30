"""This conftest.py is scoped to the root directory.

This contains fixtures that are needed by all tests during a test session.
This file also contains hooks,

To override hooks and define fixtures that are module scoped, create them
in a directory.
"""

import os
from pathlib import Path
from time import sleep

import pytest
import requests
from fixtures import *
from server_utils import setup_env, start_server, stop_server

# Build paths inside the project like this: PROJ_DIR / 'subdir'.
PROJ_DIR = Path(__file__).resolve().parent.parent


def pytest_configure():
    """Initiate configuration before test session starts.

    This will run before tests start running.
    """
    pass


def pytest_unconfigure():
    """Undo configurations and cleanup."""
    pass


@pytest.fixture(scope="module")
def set_server_environment(flask_server_path, flask_server__env, flask_server_port):
    """Create and later teardown the environment variables needed for the flask server to run."""
    old_path, old_env, old_port = setup_env(
        server_path=flask_server_path,
        server_env=flask_server__env,
        server_port=flask_server_port,
    )
    yield True
    setup_env(server_path=old_path, server_env=old_env, server_port=old_port)


@pytest.fixture(scope="module", autouse=True)
def log_server(set_server_environment):
    """Start and later teardown the flask app server."""
    if set_server_environment:
        svr_proc = start_server()
        sleep(1)
    else:
        raise ValueError("Environment not setup for flask server.")
    yield True
    code: int = stop_server(svr_proc)
    if code == 0:
        print("Server process exited with code 0.")
    elif code == None and os.environ.get("CI_TEST_ENV", "False") == "False":
        # Some CI environments can take a long time to return error codes.
        raise RuntimeError("The flask server process failed to terminate.")


@pytest.fixture(scope="module", autouse=True)
def request_session():
    """``Session`` object for connection pooling.

    Use it for GET and POST with ``requests``.
    """
    request_session = requests.Session()
    yield request_session
    request_session.close()
