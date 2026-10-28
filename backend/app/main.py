from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router

app = FastAPI(title="Kinetra API", version="0.2.0")
app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Si existe el frontend compilado, servirlo desde el mismo origen (cookies SameSite=Strict).
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        return FileResponse(_dist / "index.html")
