from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.routes import router
from .config import Config


app = FastAPI(title=Config.APP_NAME, version=Config.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "app": Config.APP_NAME, "version": Config.VERSION}


@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse("static/manifest.webmanifest", media_type="application/manifest+json")


@app.get("/service-worker.js")
async def service_worker():
    return FileResponse("static/service-worker.js", media_type="text/javascript")


@app.get("/icon.svg")
async def icon():
    return FileResponse("static/icon.svg", media_type="image/svg+xml")
