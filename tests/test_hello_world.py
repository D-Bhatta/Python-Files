"""Sample tests.

These are sample tests that should pass every time.

1. `test_always_passes` should always pass and acts as a basic sanity check of
    the entire configuration.
2. `test_hello_world` tests the return of the `hello_world` function in
    `/app/hello_world.py`. It should pass easily.
"""
from app.app import hello_world


def test_always_passes():
    """This test will always pass."""
    assert 1 == 1


def test_hello_world():
    """Tests the `hello_world` function in `/app/hello_world.py`."""
    assert hello_world(1) == 1, "Expected hello_world to return 1 with 1 input"
