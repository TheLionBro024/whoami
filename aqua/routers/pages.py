from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aqua.database import get_db
from aqua.models import User, SensorData
from aqua.security import get_current_user_optional, get_current_user, get_admin_user

router = APIRouter(tags=["pages"])

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request=request,
        name="home.html", 
        context={"request": request, "username": user.username if user else None, "is_admin": user.is_admin if user else False}
    )

@router.get("/login_page", response_class=HTMLResponse)
async def login_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@router.get("/register_page", response_class=HTMLResponse)
async def register_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="register.html", context={"request": request})

@router.get("/info", response_class=HTMLResponse)
async def info_page(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SensorData).order_by(SensorData.timestamp.desc()).limit(20))
    data = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="info.html", 
        context={"request": request, "username": user.username, "is_admin": user.is_admin, "sensor_data": data}
    )

@router.get("/confirm", response_class=HTMLResponse)
async def confirm_page(request: Request, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.is_confirmed == False))
    unconfirmed_users = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="confirm.html", 
        context={"request": request, "users": unconfirmed_users, "username": admin.username}
    )


@router.get("/live", response_class=HTMLResponse)
async def live_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="live.html", 
        context={
            "request": request, 
            "username": user.username, 
            "is_admin": user.is_admin
        }
    )

@router.get("/settings", response_class=HTMLResponse)
async def live_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="settings.html", 
        context={
            "request": request, 
            "username": user.username, 
            "is_admin": user.is_admin
        }
    )