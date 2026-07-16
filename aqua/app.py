#aqua.evolv — FastAPI application entry point for aqua.evolvplatform.com
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from aqua.database import init_db
from aqua.routers import auth, sensor, admin, export, pages, settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Evolv.Aqua",
    description="Aqua water quality monitoring system",
    lifespan=lifespan
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Routers
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(sensor.router)
app.include_router(admin.router)
app.include_router(export.router)
app.include_router(settings.router)
