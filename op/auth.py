#op.evolv — Simple password-based auth for op.evolvplatform.com
# Mirrors the aqua auth pattern: JWT cookie, bcrypt hash, no registration.
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

_OP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(_OP_DIR, ".env.op"))

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_change_me")
ALGORITHM = "HS256"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_admin_session(request: Request) -> bool:
    """Dependency: raises 401 if the op_session cookie is missing or invalid."""
    token = request.cookies.get("op_session")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/api/v1/login")
def login(req: LoginRequest, response: Response):
    if req.username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        if not bcrypt.checkpw(req.password.encode("utf-8"), ADMIN_PASSWORD_HASH.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"role": "admin"})
    response.set_cookie(
        key="op_session",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return {"message": "Login successful"}


@router.post("/api/v1/logout")
def logout(response: Response):
    response.delete_cookie("op_session")
    return {"message": "Logged out"}
