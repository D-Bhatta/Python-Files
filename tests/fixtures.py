"""Store some fixtures here to keep the rest of the test suite clean."""

import json

import pytest

from app.models import HttpUrl  # type: ignore[import]


@pytest.fixture(scope="module")
def log_data() -> list[str]:
    """Return a sample of log data for testing."""
    with open("tests/data/log_data.json", encoding="utf-8") as fp:
        json_data: list[dict[str, str]] = json.load(fp)
    data: list[str] = []
    for log in json_data:
        data.append(json.dumps(log))
    return data


@pytest.fixture(scope="module")
def flask_server__env():
    """Return the environment the flask server will run in.

    Can be ``development`` or ``production``.
    """
    return "production"


@pytest.fixture(scope="module")
def flask_server_path():
    """Path to flask app file."""
    return "app/app_server.py"


@pytest.fixture(scope="module")
def flask_server_port():
    """Return the flask server port.

    Usually:
    1. 3000
    2. 5000
    3. 8000
    4. 8080
    """
    return "3000"


@pytest.fixture(scope="module")
def n_generator():
    """Return a generator object that yields valid namespaces."""

    def _n_generator():
        """Generate 30 namespaces."""
        namespaces = [
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
        for namespace in namespaces:
            yield namespace

    _ngen = _n_generator()
    return _ngen


@pytest.fixture
def n_space(n_generator):
    """Return a valid namespace."""
    try:
        return next(n_generator)
    except StopIteration:
        raise ValueError("Add more namespaces to the list of namespaces.")
