import pytest
from fastapi.testclient import TestClient

from app.main import app as main_app


@pytest.fixture
def client():
    return TestClient(main_app)


def test_root_returns_service_info(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert isinstance(data["endpoints"], dict)
    assert data["endpoints"]["chat"] == "/v1/chat/completions"


def test_v1_root_and_trailing_slash(client):
    for path in ["/v1", "/v1/"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["api_version"] == "v1"
        assert isinstance(data["endpoints"], dict)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_tools_empty_list(client):
    response = client.get("/api/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["tools"] == []