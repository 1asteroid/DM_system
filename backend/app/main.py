from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .api import api_router, app_router
from .core.config import PROJECT_ROOT
from .core.database import init_db


FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Diplom Monitoring API", lifespan=lifespan)
app.include_router(api_router)
app.include_router(app_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    """Serve the built React app from frontend/dist, with SPA fallback."""
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
        raise HTTPException(status_code=404, detail="Not Found")

    if not FRONTEND_INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found")

    if full_path:
        candidate = (FRONTEND_DIST_DIR / Path(full_path)).resolve()
        try:
            candidate.relative_to(FRONTEND_DIST_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not Found")
        if candidate.is_file():
            return FileResponse(candidate)

    return FileResponse(FRONTEND_INDEX_FILE)
