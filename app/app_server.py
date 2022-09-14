"""App server that acts as a stand-in for a logging solution."""
import json
from typing import Any
from uuid import uuid4

from flask import Flask, request

app = Flask(__name__)


REQUEST_DATA: dict[Any, Any] = {}  # TODO: Find a better type for this annotation.

_namespaces = [
    "4c4de413-bfbe-4024-9c5c-ae8cc7bf636a",
    "36558194-c511-4a77-9c98-6e9a632907c6",
    "97ff754e-7b16-41f6-aafb-31948c87d1b8",
    "c3add815-614c-4a03-8660-17a222ec0d8f",
    "0b626a39-0204-4174-991d-c925f0777014",
    "8cb7bb55-d795-40e7-94d3-7e9242b69d2e",
    "07cae401-b19b-46bd-8d77-27bb9f06326e",
    "b5b098ee-c08b-416c-9356-358493a1e000",
    "eafc73d2-12ee-42ca-bafa-8fc53e03de1b",
    "af946349-a830-47d9-828c-d4fd15aef098",
    "cbd05d5a-c85a-4daf-8fd2-9471849bd881",
    "1ff1ec16-8e5e-4f8a-9b1d-ba10e3236ffd",
    "22278722-5b7e-4a34-9617-6bc5d765c27a",
    "8358e3d2-2b4e-470b-942d-71eef8b68b8f",
    "4ffb3164-905c-482b-831b-6958d6fbad28",
    "23399c07-3e8b-4161-af64-25305e6fb07b",
    "742d914a-48ba-49fe-a9df-c0f5fc5939f1",
    "899e8341-9e76-4e67-adf8-61d6ad5ebc80",
    "05cee863-863b-44b4-9db4-92168603d06b",
    "10c72d11-2073-4f70-b38c-f4ae48915b42",
    "390c4207-1fc0-4f81-9148-beff68e1619a",
    "7ae55803-7249-444c-bf6d-e1814c4ff565",
    "2d72f938-f63c-4939-844f-8e285d696adf",
    "e554f389-fcf8-45eb-ace1-fc74f8e53de2",
    "bd31c037-773e-47b0-8dd4-8b089a405b1a",
    "c92c9d4c-f7ff-4834-94b7-77979d6ae252",
    "76fb93ee-a829-49c6-9f6b-6be0acc391ab",
    "a1f34d1d-0125-4456-ac4e-4c012892ea99",
    "2d2751cc-a83a-48c9-8efe-231cec5d517a",
    "d16fce4c-4fa6-4b09-8dde-d048dc7fe4e0",
]

# Create some namespaces for easy testing.
for ns in _namespaces:
    REQUEST_DATA[ns] = []


@app.route("/", methods=["GET", "POST"])
def home():
    """Health check."""
    return "OK", 200


@app.route("/log/", methods=["GET", "POST"])
def log():
    """Stub function that returns a message.

    Doesn't store data in POST request body.

    Args:
        namespace: The namespace that the logs are stored under.

    Returns:
        str: For a GET or POST request, return stub confirmation message.


    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:5000/log/"
        ... )
        >>> response.text
        Logger at 0004a334-ef94-4570-9107-8f0016bd6b59/
        >>> response = requests.post(
        ...     "http://localhost:5000/log/",
        ...     data='{"time": "2022-06-06 09:39:40,626", "log_level": "CRITICAL", "line": "39", "name": "__main__", "processID": "3856", "message": "This is critical"}'
        ... )
        >>> response.text
        Received JSON Data as POST
    """  # noqa: B950
    if request.method == "GET":
        return "logger", 200
    if request.method == "POST":
        return "Received JSON Data as POST", 200


@app.route("/log/namespaces/", methods=["GET"])
def create_namespace():
    """Return a unique namespace.

    Returns:
        str: For a GET request, returns a namespace.

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:5000/log/namespaces/"
        ... )
        >>> response.text
        0004a334-ef94-4570-9107-8f0016bd6b59
    """
    namespace = str(uuid4())
    REQUEST_DATA[namespace] = []
    return namespace, 200


@app.route("/log/namespaces/<namespace>/", methods=["GET", "POST"])
def log_namespace(namespace: str = None):
    """Store log records in a namespace.

    POST request data should contains logs formatted as JSON.

    Args:
        namespace: The namespace that the logs are stored under.

    Returns:
        str: For a GET request, returns the logger namespace.
        For a POST request, returns confirmation message.

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:5000/log/0004a334-ef94-4570-9107-8f0016bd6b59/"
        ... )
        >>> response.text
        Logger at 0004a334-ef94-4570-9107-8f0016bd6b59/
        >>> response = requests.post(
        ...     "http://localhost:5000/log/0004a334-ef94-4570-9107-8f0016bd6b59/",
        ...     data='{"time": "2022-06-06 09:39:40,626", "log_level": "CRITICAL", "line": "39", "name": "__main__", "processID": "3856", "message": "This is critical"}'
        ... )
        >>> response.text
        Received JSON Data as POST
    """  # noqa: B950
    if request.method == "GET":
        log_tag_msg = f"Logger at {namespace}"
        return log_tag_msg, 200
    if request.method == "POST":
        json_data = request.get_json()
        try:
            REQUEST_DATA[namespace].append(json_data)
        except KeyError:
            err_msg = "This namespace doesn't exist."
            return err_msg, 404
        confirm_msg = f"Received JSON Data as POST for {namespace}"
        return confirm_msg, 200


@app.route("/log/data/<namespace>/", methods=["GET"])
def get_log_data(namespace: str):
    """Respond with all log data stored from requests in a namespace.

    Response data contains logs formatted as JSON.

    Args:
        namespace: The namespace that the logs are stored under.

    Returns:
        json: Log data stored as json.

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:5000/log/data/0004a334-ef94-4570-9107-8f0016bd6b59/"
        ... )
        >>> dict(response.json())
        {"time": "2022-06-06 09:39:40,626", "log_level": "CRITICAL", "line": "39", "name": "__main__", "processID": "3856", "message": "This is critical"}
    """  # noqa: B950
    try:
        json_log_data = json.dumps({namespace: REQUEST_DATA[namespace]})
    except KeyError:
        err_msg = "This namespace doesn't exist."
        return err_msg, 404
    return json_log_data, 200


@app.route("/log/clean/<namespace>/")
def clean_request_data(namespace: str):
    """Delete all stored request data.

    Response text contains message with number of deleted logs.

    Args:
        namespace: The namespace that the logs are stored under.

    Returns:
        str: Log deletion message. Contains number of deleted logs and the
        namespace it is deleted from.

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:5000/log/clean/0004a334-ef94-4570-9107-8f0016bd6b59/"
        ... )
        >>> response.text
        Deleted 100 logs in 0004a334-ef94-4570-9107-8f0016bd6b59.
    """
    try:
        deleted = len(REQUEST_DATA[namespace])
    except KeyError:
        err_msg = "This namespace doesn't exist."
        return err_msg, 404
    REQUEST_DATA[namespace] = []
    clean_msg = f"Deleted {deleted} logs in {namespace}."
    return clean_msg, 200
