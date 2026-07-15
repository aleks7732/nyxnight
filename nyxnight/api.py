"""FastAPI application for standalone NyxNight."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from nyxnight.models import PlanRequest, PlanResponse
from nyxnight.planner import create_plan

WEB_DIR = Path(__file__).resolve().parent / "web"


def create_app() -> FastAPI:
    app = FastAPI(
        title="NyxNight",
        version="0.1.0",
        description="Standalone deterministic night-out planner",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "nyxnight", "mode": "demo"}

    @app.post("/api/plan", response_model=PlanResponse)
    async def plan(request: PlanRequest) -> PlanResponse:
        return create_plan(request)

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    return app


app = create_app()
