def test_health_and_documentation(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    assert "/health" in client.get("/openapi.json").json()["paths"]
