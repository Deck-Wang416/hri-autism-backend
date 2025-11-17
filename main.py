from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.auth import router as auth_router
from api.routers.children import router as children_router
from api.routers.sessions import router as sessions_router
from common.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="HRI Autism Backend",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(children_router)
    app.include_router(sessions_router)

    @app.get("/healthz", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
