from __future__ import annotations

import contextlib
import os
import socket

import uvicorn

from .config import settings
from .main import app


def _is_port_free(host: str, port: int) -> bool:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.connect_ex((host, port)) != 0


def _pick_port(host: str, start_port: int, tries: int = 50) -> int:
    port = int(start_port)
    for _ in range(max(1, tries)):
        if _is_port_free(host, port):
            return port
        port += 1
    return start_port


def main() -> None:
    host = os.getenv("ANT_PVG_HOST", settings.host)
    base_port = int(os.getenv("ANT_PVG_PORT", str(settings.port)))

    port = _pick_port(host, base_port, tries=50)
    url = f"http://{host}:{port}"

    if port != base_port:
        print(f"[ant-pvg] Port {base_port} is busy; selected free port {port}.")
    print(f"[ant-pvg] Starting ANT–PVG Research Observatory at {url}")
    print(f"[ant-pvg] API docs available at {url}/docs")

    # Run uvicorn directly against the imported FastAPI app. No need for --app-dir.
    uvicorn.run(app, host=host, port=port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
