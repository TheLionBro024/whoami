#aqua.evolv
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aqua.database import get_db
from aqua.models import User
from aqua.security import verify_password, create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalars().first()
    
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not user.is_confirmed:
        raise HTTPException(status_code=401, detail="User not confirmed. Please wait for an admin to approve your account.")
        
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    response.set_cookie(
        key="aqua_session",
        value=access_token,
        httponly=True,
        secure=False, # Set to true in prod with HTTPS
        samesite="lax",
        max_age=7*24*3600
    )
    return {"status": "success", "message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("aqua_session")
    return {"status": "success", "message": "Logged out"}

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check existing user
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="User already exists")
        
    from aqua.security import get_password_hash
    new_user = User(
        username=req.username,
        password=get_password_hash(req.password)
    )
    
    db.add(new_user)
    await db.commit()
    
    # TODO: Send registration email to admins
    # send_registration_notification(new_user)
    
    return {"status": "success", "message": "Registration successful. Please wait for an admin to confirm your account."}
