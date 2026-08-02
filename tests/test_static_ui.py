"""اختبارات تقديم الواجهة من FastAPI بعد سحب الخادم القياسي."""

import pytest
from ant_pvg_observatory.main import STATIC_ROOT, app
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_index_is_served_from_the_application(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "ANT–PVG" in response.text


@pytest.mark.parametrize(
    "asset",
    [
        "app.js",
        "app.css",
        "vendor/katex/katex.min.js",
        "vendor/katex/katex.min.css",
        "vendor/katex/fonts/KaTeX_Main-Regular.woff2",
    ],
)
def test_bundled_assets_are_reachable(client: TestClient, asset: str) -> None:
    """أصول KaTeX مُضمَّنة: المنصة تعمل بلا اتصال بالشبكة."""
    assert client.get(f"/{asset}").status_code == 200


def test_paths_outside_the_static_root_are_refused(client: TestClient) -> None:
    assert client.get("/nope.txt").status_code == 404
    assert client.get("/%2e%2e/pyproject.toml").status_code == 404


def test_api_routes_are_not_shadowed_by_the_catch_all(client: TestClient) -> None:
    """المسار الشامل للواجهة يجب ألا يبتلع مسارات API."""
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/source-layers").status_code == 200


def test_the_standalone_server_is_gone() -> None:
    """مسار واحد للصيانة: لا خادم قياسي موازٍ."""
    repository_root = STATIC_ROOT.parent
    assert not (repository_root / "server.py").exists()
    assert not (repository_root / "start_windows.bat").exists()
