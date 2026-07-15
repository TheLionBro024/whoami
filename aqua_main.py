import asyncio
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

# We will import our routers and database setup here
from aqua.database import init_db
from aqua.routers import auth, sensor, admin, export, pages

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Evolv.Aqua", description="Aqua monitoring system", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "aqua", "static")

if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(sensor.router)
app.include_router(admin.router)
app.include_router(export.router)

if __name__ == "__main__":
    uvicorn.run("aqua_main:app", host="0.0.0.0", port=5000, reload=True)
