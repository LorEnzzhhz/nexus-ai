from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

from .api.routes import router
from .config import Config


async def app_health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "app": Config.APP_NAME, "version": Config.VERSION})


async def manifest(request):
    return FileResponse("static/manifest.webmanifest", media_type="application/manifest+json")


async def service_worker(request):
    return FileResponse("static/service-worker.js", media_type="text/javascript")


async def icon(request):
    return FileResponse("static/icon.svg", media_type="image/svg+xml")


app = Starlette(
    debug=Config.DEBUG,
    routes=[
        Mount("/api", app=router),
        Route("/", FileResponse("static/index.html")),
        Route("/health", app_health),
        Route("/manifest.webmanifest", manifest),
        Route("/service-worker.js", service_worker),
        Route("/icon.svg", icon),
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
