from ant_pvg_observatory.main import app
from fastapi.testclient import TestClient


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_source_layers_are_separated() -> None:
    with TestClient(app) as client:
        response = client.get("/api/source-layers")
    keys = {item["key"] for item in response.json()}
    assert keys == {"ENCYCLOPEDIA", "MODEL_SYNTHESIS", "LITERATURE"}
