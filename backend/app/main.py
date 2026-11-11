"""
EVANGELINE FastAPI entrypoint.

Serves the API under /api/* and the vanilla frontend as static files.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import auth_routes, chat_routes, config_routes, health

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth_routes.router)
app.include_router(config_routes.router)
app.include_router(chat_routes.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ----- Static frontend (splash / login / app / settings) -----

if FRONTEND_DIR.is_dir():
    # Mount assets first so /css and /js resolve
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/")
    def splash() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/login")
    def login_page() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "login.html")

    @app.get("/app")
    def app_page() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "app.html")

    @app.get("/settings")
    def settings_page() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "settings.html")
