from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings.library_root.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0-dev", lifespan=lifespan)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/source-layers", tags=["governance"])
def source_layers() -> list[dict[str, str]]:
    return [
        {
            "key": "ENCYCLOPEDIA",
            "authority": "INTERNAL_CURATED",
            "rule": "Content imported from the governed encyclopedia corpus.",
        },
        {
            "key": "MODEL_SYNTHESIS",
            "authority": "UNVERIFIED_UNTIL_SOURCED",
            "rule": "May suggest links and questions but cannot certify a claim.",
        },
        {
            "key": "LITERATURE",
            "authority": "EXTERNAL_VERIFIED",
            "rule": "Requires traceable bibliographic evidence and reading status.",
        },
    ]
