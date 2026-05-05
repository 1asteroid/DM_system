from fastapi import FastAPI

from .api import api_router, app_router
from .core.database import init_db

app = FastAPI(title="Diplom Monitoring API")
app.include_router(api_router)
app.include_router(app_router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
