from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from guardweave.api.routes import router

logger = logging.getLogger("guardweave.api")


def create_app() -> FastAPI:
    app = FastAPI(
        title="GuardWeave API",
        description="Safety, Guardrails & Governance Layer for AI Agents",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.on_event("startup")
    async def startup():
        from guardweave.persistence.database import init_db
        await init_db()
        logger.info("GuardWeave API started")

    return app
