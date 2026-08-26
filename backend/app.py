from __future__ import annotations

from fastapi import FastAPI

from backend.routes.auth_routes import router as auth_router
from backend.routes.document_routes import router as document_router
from backend.routes.form_routes import router as form_router
from backend.routes.profile_routes import router as profile_router

app = FastAPI(
    title="Major Project Unified API",
    version="1.0.0",
    description="Unified FastAPI backend with the working document extraction service plus placeholder routes for future integration.",
)

app.include_router(document_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(form_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
