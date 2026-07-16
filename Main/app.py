# Main.evolv — Main landing page for evolvplatform.com (port 8000)
import os

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

_MAIN_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Evolv.Main", description="evolvplatform.com landing page")

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    path = request.url.path.lower()
    if "/.git" in path or "/.env" in path:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return await call_next(request)


app.mount("/static", StaticFiles(directory=os.path.join(_MAIN_DIR, "static")), name="main_static")


@app.get("/")
def read_root():
    return FileResponse(os.path.join(_MAIN_DIR, "static", "index.html"))
