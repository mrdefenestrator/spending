"""Shared fixtures for e2e Playwright tests."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 10.0) -> None:
    """Block until the Flask server is accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f"Flask server did not start on port {port}")


@pytest.fixture(scope="session")
def flask_server(tmp_path_factory):
    """Start Flask on a random port with a temp SQLite database.

    Yields the base URL (e.g. ``http://127.0.0.1:54321``).
    The server is torn down after the test session.
    """
    port = _free_port()
    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test.db"

    env = {
        **os.environ,
        "SPENDING_DB": str(db_path),
        "SPENDING_PORT": str(port),
        "FLASK_DEBUG": "0",
    }

    proc = subprocess.Popen(
        [sys.executable, "-m", "web.app"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _wait_for_server(port)
    except TimeoutError:
        proc.terminate()
        proc.wait(timeout=5)
        raise

    yield f"http://127.0.0.1:{port}"

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture(autouse=True)
def _set_default_timeout(page):
    """Use a short default timeout so test failures are fast."""
    page.set_default_timeout(5000)
