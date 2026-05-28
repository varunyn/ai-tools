def test_root_returns_service_info(get_json_ok):
    data = get_json_ok("/")
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


def test_health_endpoint(get_json_ok):
    data = get_json_ok("/health")
    assert data["status"] == "healthy"
