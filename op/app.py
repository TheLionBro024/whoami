#op.evolv — FastAPI application entry point for op.evolvplatform.com (port 8001)
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import op.serve as serve
from op.auth import router as auth_router
from op.blog import router as blog_router

_OP_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure folder structure and generate static pages on startup
    serve.init_folders()
    posts = serve.load_posts()
    serve.regenerate_all(posts)
    yield


app = FastAPI(title="Evolv.op", description="op.evolvplatform.com — Personal site & blog", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Security middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    path = request.url.path.lower()
    if "/.git" in path or "/.env" in path:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return await call_next(request)


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(blog_router)


# ---------------------------------------------------------------------------
# HTML page routes
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return FileResponse(os.path.join(_OP_DIR, "templates", "index.html"))


@app.get("/blog")
def read_blog():
    return FileResponse(os.path.join(_OP_DIR, "templates", "blog.html"))


@app.get("/admin")
def read_admin():
    return FileResponse(os.path.join(_OP_DIR, "templates", "admin.html"))


# ---------------------------------------------------------------------------
# Static file mounts (order matters — more specific first)
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory=os.path.join(_OP_DIR, "static")), name="op_static")
app.mount("/blog_assets", StaticFiles(directory=os.path.join(_OP_DIR, "blog_assets")), name="blog_assets")
app.mount("/posts", StaticFiles(directory=os.path.join(_OP_DIR, "posts")), name="op_posts")
app.mount("/gallery", StaticFiles(directory=os.path.join(_OP_DIR, "gallery")), name="op_gallery")
