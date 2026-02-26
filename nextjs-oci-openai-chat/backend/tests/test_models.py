# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnusedParameter=false
import pytest
from fastapi.testclient import TestClient

from app.main import app as main_app


@pytest.fixture()
def client():
    return TestClient(main_app)


def test_api_chat_models_returns_available_models(client):
    response = client.get("/api/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0


def test_v1_models_openai_list_shape(client):
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    for model in data["data"]:
        assert "id" in model
        assert "object" in model
        assert model["object"] == "model"
        assert "created" in model
        assert "owned_by" in model
        assert "permission" in model
        assert "root" in model
        assert "parent" in model


def test_v1_tags_ollama_shape(client):
    response = client.get("/v1/tags")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0
    for model in data["models"]:
        assert "name" in model
        assert "model" in model
        assert "details" in model
        assert isinstance(model["details"], dict)