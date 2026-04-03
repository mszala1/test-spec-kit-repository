from unittest.mock import patch

from fastapi.testclient import TestClient

from src.services.exceptions import UpstreamError


def test_get_ip_happy_path(client: TestClient) -> None:
    response = client.get("/ip", headers={"X-Forwarded-For": "1.2.3.4"})
    assert response.status_code == 200
    data = response.json()
    assert data["ip"] == "1.2.3.4"


def test_get_ip_falls_back_to_x_real_ip(client: TestClient) -> None:
    response = client.get("/ip", headers={"X-Real-IP": "5.6.7.8"})
    assert response.status_code == 200
    assert response.json()["ip"] == "5.6.7.8"


def test_get_ip_prefers_x_forwarded_for_over_x_real_ip(client: TestClient) -> None:
    response = client.get(
        "/ip",
        headers={"X-Forwarded-For": "1.2.3.4, 10.0.0.1", "X-Real-IP": "5.6.7.8"},
    )
    assert response.status_code == 200
    assert response.json()["ip"] == "1.2.3.4"


def test_get_ip_uses_first_ip_from_forwarded_for_list(client: TestClient) -> None:
    response = client.get("/ip", headers={"X-Forwarded-For": "9.9.9.9, 10.0.0.1, 172.16.0.1"})
    assert response.status_code == 200
    assert response.json()["ip"] == "9.9.9.9"


def test_get_ip_returns_detail_on_failure(client: TestClient) -> None:
    # Mock the IP extraction service to raise an UpstreamError
    with patch("src.routers.ip.extract_caller_ip") as mock_extract:
        mock_extract.side_effect = UpstreamError("Could not determine caller IP address")
        response = client.get("/ip")
        assert response.status_code == 502
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Could not determine caller IP address"