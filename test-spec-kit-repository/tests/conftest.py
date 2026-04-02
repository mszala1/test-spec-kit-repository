from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_httpx_get():
    """Patch httpx.get for upstream call mocking."""
    with patch("httpx.get") as mock:
        yield mock


def make_httpx_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Helper to create a mock httpx response."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status = MagicMock()
    return response
