from unittest.mock import MagicMock

import pytest

from src.services.exceptions import UpstreamError
from src.services.ip_service import extract_caller_ip


def _make_request(
    xff: str | None = None,
    x_real_ip: str | None = None,
    client_host: str | None = "127.0.0.1",
) -> MagicMock:
    request = MagicMock()
    headers = {}
    if xff is not None:
        headers["x-forwarded-for"] = xff
    if x_real_ip is not None:
        headers["x-real-ip"] = x_real_ip
    request.headers = headers
    if client_host:
        request.client = MagicMock()
        request.client.host = client_host
    else:
        request.client = None
    return request


def test_extract_ip_from_x_forwarded_for() -> None:
    request = _make_request(xff="1.2.3.4")
    assert extract_caller_ip(request) == "1.2.3.4"


def test_extract_ip_uses_first_ip_from_xff_list() -> None:
    request = _make_request(xff="1.2.3.4, 10.0.0.1, 172.16.0.1")
    assert extract_caller_ip(request) == "1.2.3.4"


def test_extract_ip_prefers_x_forwarded_for_over_x_real_ip() -> None:
    request = _make_request(xff="1.2.3.4", x_real_ip="5.6.7.8")
    assert extract_caller_ip(request) == "1.2.3.4"


def test_extract_ip_falls_back_to_x_real_ip() -> None:
    request = _make_request(x_real_ip="5.6.7.8")
    assert extract_caller_ip(request) == "5.6.7.8"


def test_extract_ip_falls_back_to_client_host() -> None:
    request = _make_request(client_host="9.9.9.9")
    assert extract_caller_ip(request) == "9.9.9.9"


def test_extract_ip_raises_upstream_error_when_all_sources_absent() -> None:
    request = _make_request(client_host=None)
    with pytest.raises(UpstreamError) as exc_info:
        extract_caller_ip(request)
    assert "Could not determine caller IP address" in exc_info.value.message