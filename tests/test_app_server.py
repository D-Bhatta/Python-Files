"""Test the flask app at app/app_server.py."""
import asyncio
import json
import re

import pytest
from aiohttp import ClientSession
from fixtures import n_space
from requests import Response

from app.models import HttpUrl  # type: ignore[import]  # Ignore missing imports


def test_home(flask_server_port, request_session):
    """Test GET request at ``home_url``."""
    home_url = HttpUrl(url=f"http://localhost:{flask_server_port}/")
    uri_str = str(home_url.url)
    response = request_session.get(uri_str)
    response_text: str = response.text
    assert response_text == "OK", "Fix the home endpoint response text."
    assert response.status_code == 200, "Home endpoint isn't returning 200 as status."


def test_log_get(flask_server_port, request_session):
    """Test GET request at ``log_url``."""
    log_url = HttpUrl(url=f"http://localhost:{flask_server_port}/log/")
    uri_str = str(log_url.url)
    response = request_session.get(uri_str)
    confirmation_msg: str = response.text
    assert confirmation_msg == "logger", "Fix the log stub GET confimation message."
    assert (
        response.status_code == 200
    ), "Log stub endpoint isn't returning 200 as status on GET."


def test_log_post(flask_server_port, request_session):
    """Test POST request with test data at ``log_url``."""
    log_url = HttpUrl(url=f"http://localhost:{flask_server_port}/log/")
    uri_str = str(log_url.url)
    response = request_session.post(
        uri_str,
        data=(
            json.dumps(
                {
                    "time": "2022-06-06 09:39:40,626",
                    "log_level": "CRITICAL",
                    "line": "39",
                    "name": "__main__",
                    "processID": "3856",
                    "message": "This is critical",
                }
            )
        ),
    )
    response_text: str = response.text
    assert (
        response_text == "Received JSON Data as POST"
    ), "Fix the log stub POST confimation message."
    assert (
        response.status_code == 200
    ), "Log stub endpoint isn't returning 200 as status on POST."


def uuidv4_validator(uuid_str: str):
    """Check if passed str is a valid UUID v4."""
    UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    re_machine = re.compile(UUID_RE)
    if re_machine.match(uuid_str) and len(uuid_str) == 36:
        return True
    return False


@pytest.mark.parametrize(
    ("uuid_str", "is_uuid", "fail_msg", "test_num"),
    [
        (
            "0004a334-ef94-4570-9107-8f0016bd6b59",
            True,
            "This valid uuid v4 should pass.",
            1,
        ),
        (
            "b1d8ee61-12e3-421f-a8eb-121cb84a0017",
            True,
            "This valid uuid v4 should pass.",
            2,
        ),
        (
            "20f5484b-88ae-49b0-8af0-3a389b4917dd",
            True,
            "This valid uuid v4 should pass.",
            3,
        ),
        (
            "2b1eb780-8a03-4031-b1e5-2f7674c60df3",
            True,
            "This valid uuid v4 should pass.",
            4,
        ),
        (
            "0004a334-ef94-3570-9107-8f0016bd6b59",
            False,
            "Missing 4 in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has 3.",
            5,
        ),
        (
            "0004a334-ef94-h570-9107-8f0016bd6b59",
            False,
            "Missing 4 in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has h.",
            6,
        ),
        (
            "0004a334-ef94-4570-7107-8f0016bd6b59",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has 7.",
            7,
        ),
        (
            "b1d8ee61-12e3-421f-68eb-121cb84a0017",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has 6.",
            8,
        ),
        (
            "b1d8ee61-12e3-421f-p8eb-121cb84a0017",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has p.",
            9,
        ),
        (
            "b1d8ee61-12e3-421f-q8eb-121cb84a0017",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has q.",
            10,
        ),
        (
            "20f5484b-88ae-49b0-1af0-3a389b4917dd",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has 1.",
            11,
        ),
        (
            "20f5484b-88ae-49b0-2af0-3a389b4917dd",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has 2.",
            12,
        ),
        (
            "20f5484b-88ae-49b0-maf0-3a389b4917dd",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has m.",
            13,
        ),
        (
            "2b1eb780-8a03-4031-n1e5-2f7674c60df3",
            False,
            "Invalid y:{8,9,a,b} in xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, has n.",
            14,
        ),
        (
            "2b1eb780-8a03-4031-b1e5-2f7674c60df3d",
            False,
            "Length should be 36 instead of 37",
            15,
        ),
        (
            "2b1eb780-8a03-4031-b1e5-2f7674c60df3-",
            False,
            "Length should be 36 instead of 37",
            16,
        ),
        (
            "2b1eb780-8a03-4031-b1e5-2f7674c60df3-j",
            False,
            "Length should be 36 instead of 38",
            17,
        ),
        (
            "2b1eb780-8a03-4031-b1e5-2f7674c6df3",
            False,
            "Length should be 36 instead of 35",
            18,
        ),
    ],
)
def test_uuidv4_validator(uuid_str: str, is_uuid: bool, fail_msg: str, test_num: int):
    """Check if namespace is a valid uuid V4 string."""
    matched = uuidv4_validator(uuid_str=uuid_str)
    test_num_str = f"Test number: {test_num}: "
    test_failure_msg = test_num_str + fail_msg
    assert matched == is_uuid, test_failure_msg


def test_namespace_validity(flask_server_port, request_session):
    """Test if ``namespace_url`` returns a valid namespace in response."""
    namespace_url = HttpUrl(url=f"http://localhost:{flask_server_port}/log/namespaces/")
    uri_str = str(namespace_url.url)
    response = request_session.get(uri_str)
    assert (
        uuidv4_validator(response.text) == True
    ), "Namespace is not a valid uuid v4 string."


async def get_async_response_text(uri: HttpUrl, session: ClientSession) -> str:
    """Send async request with session and return response text."""
    uri_str = str(uri.url)
    async with session.get(uri_str) as response:
        response_text = await response.text()
        return response_text


async def get_namespaces(namespace_url: HttpUrl, num: int = 1) -> list[str]:
    """Get ``num`` namespaces from ``namespace_url``."""
    async with ClientSession() as session:
        tasks = []
        for _ in range(0, num):
            tasks.append(
                asyncio.create_task(get_async_response_text(namespace_url, session))
            )
        namespaces = await asyncio.gather(*tasks)
        return namespaces


def test_check_namespace_uniqueness(flask_server_port):
    """Checks namespace uniqueness."""
    num_namespaces = 1000
    namespace_url = HttpUrl(url=f"http://localhost:{flask_server_port}/log/namespaces/")
    namespaces = set(
        asyncio.run(get_namespaces(namespace_url=namespace_url, num=num_namespaces))
    )
    assert (
        len(namespaces) == num_namespaces
    ), f"There's duplicate namespaces, instead of {num_namespaces} unique ones."


def test_log_namespace_get(
    flask_server_port,
    request_session,
    n_space,
):
    """Test GET request at namespace ``log_url``."""
    namespace: str = n_space

    log_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/namespaces/{namespace}/"
    )
    uri_str = str(log_url.url)
    response = request_session.get(uri_str)
    confirmation_msg = response.text
    assert (
        response.status_code == 200
    ), "Logging at namespace endpoint isn't returning 200 as status on GET."
    assert (
        confirmation_msg == f"Logger at {namespace}"
    ), "Fix the confirmation message for logging at namespace endpoint."


def test_log_retrieve_and_delete(flask_server_port, request_session, n_space):
    """Test log storage, retrieval, and deletion."""
    namespace: str = n_space

    log_data = json.dumps(
        {
            "time": "2022-06-06 09:39:40,626",
            "log_level": "CRITICAL",
            "line": "39",
            "name": "__main__",
            "processID": "3856",
            "message": "This is critical",
        }
    )

    log_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/namespaces/{namespace}/"
    )
    log_uri_str = str(log_url.url)
    log_response = request_session.post(
        log_uri_str,
        json=log_data,
    )
    log_confirmation_msg = log_response.text

    data_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/data/{namespace}/"
    )
    data_url_str = str(data_url.url)
    data_response: Response = request_session.get(data_url_str)
    try:
        data_dict = data_response.json()
        data_str = data_dict[namespace][0]
    except json.JSONDecodeError:
        data_str = data_response.text
    except KeyError:
        data_str = data_response.text

    deletion_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/clean/{namespace}"
    )
    deletion_url_str = str(deletion_url.url)
    deletion_response = request_session.get(deletion_url_str)
    deletion_confirmation_msg = deletion_response.text

    assert (
        log_confirmation_msg == f"Received JSON Data as POST for {namespace}"
    ), "Fix the confirmation message for storing log data at namespace endpoint."
    assert (
        log_response.status_code == 200
    ), "Logging at namespace endpoint isn't returning 200 as status on POST."
    assert data_str == log_data, "Stored log data and retrieved log data mismatch."
    assert (
        data_response.status_code == 200
    ), "Log data retrieval endpoint isn't returning 200 as status on GET."
    assert (
        deletion_confirmation_msg == f"Deleted 1 logs in {namespace}."
    ), "Fix log data deletion confirmation message."
    assert (
        deletion_response.status_code == 200
    ), "Log data deletion endpoint isn't returning 200 as status on GET."
