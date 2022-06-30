"""Contains functions to manage the flasks server process."""
from __future__ import annotations  # Remove when py3.9 is deprecated

import os
import subprocess
import sys
from time import sleep


def setup_env(
    server_path: str, server_env: str, server_port: str
) -> tuple[str, str, str]:
    """Set the environment variables for the flask server process.

    Set the environment variables and return the old variables.

    Args:
        server_path: The path to the flask app.
        server_env: The environment the flask server will run in. Can be
            ``development`` or ``production``.
        server_port: The port the flask server will serve.

    Returns:
        tuple[str]: A ``tuple`` of 3 ``str`` that represents the the old flask
        server path, the old flask server env, and the old flask server port
        environment variables.

    Examples:
        This function can be used to set and rewind the environment variables
        both.

        >>> old_path, old_env, old_port = setup_env(
        ...     server_path="app/app_server.py", server_env="development", server_port="3000"
        ... )
        >>> setup_env(server_path=old_path, server_env=old_env, server_port=old_port)
    """
    try:
        old_FLASK_APP = os.environ["FLASK_APP"]
    except KeyError:
        old_FLASK_APP = ""

    try:
        old_FLASK_ENV = os.environ["FLASK_ENV"]
    except KeyError:
        old_FLASK_ENV = ""

    try:
        old_FLASK_RUN_PORT = os.environ["FLASK_RUN_PORT"]
    except KeyError:
        old_FLASK_RUN_PORT = ""

    os.environ["FLASK_APP"] = server_path
    os.environ["FLASK_ENV"] = server_env
    os.environ["FLASK_RUN_PORT"] = server_port
    return old_FLASK_APP, old_FLASK_ENV, old_FLASK_RUN_PORT


def start_server():
    """Start the flask server process and return the ``Popen`` object.

    Returns:
        Popen: The flask server process running in the background.

    Examples:
        >>> svr_proc = start_server()
        >>> print(svr_proc)
        <Popen: returncode: None args: ['C:/Python-Files/...>
    """
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "flask",
            "run",
        ],
    )
    return server_process


def stop_server(server_process) -> int | None:
    """Stop the passed server process.

    Terminates the server process and returns a code from the server process
    after termination.

    Args:
        server_process: The running server process.

    Returns:
        int: The code returned from the terminated server process. Generally
        it can be expected to be 1 from a running process.

        If the terminated process doesn't return a code, ``None`` is returned.

    Examples:
        Pass a ``Popen`` object as the only argument.

        >>> code = stop_server(svr_proc)
        >>> if code:
        ...     print(code)
        1
    """
    # Assume unterminated process, and terminate it. On POSIX this sends
    # SIGTERM and on Windows the Win32 API function TerminateProcess()
    # is called
    server_process.terminate()
    return_code: int = server_process.poll()
    if return_code != None:
        return return_code
    # wait a minimum amount of time possible for the process to terminate
    sleep(0.2)
    return_code = server_process.poll()
    if return_code != None:
        return return_code
    # Couldn't get return code
    return None
