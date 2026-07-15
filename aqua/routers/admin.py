from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from aqua.database import get_db
from aqua.models import User, SensorData
from aqua.security import get_admin_user, get_current_user
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(tags=["admin"])

@router.post("/confirm_user/{user_id}")
async def confirm_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user:
        user.is_confirmed = True
        await db.commit()
        return {"status": "success", "message": "User confirmed"}
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/decline_user/{user_id}")
async def decline_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user:
        await db.delete(user)
        await db.commit()
        return {"status": "success", "message": "User declined and deleted"}
    raise HTTPException(status_code=404, detail="User not found")


class ClearDbInput(BaseModel):
    start_time: datetime
    end_time: datetime

@router.post("/api/clear_db")
async def clear_db(req: ClearDbInput, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_admin_user)):
    if req.start_time >= req.end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time")
    
    # Delete sensor data within the time range
    await db.execute(
        delete(SensorData)
        .where(SensorData.timestamp >= req.start_time)
        .where(SensorData.timestamp <= req.end_time)
    )
    await db.commit()
    return {"status": "success", "message": "Database cleared for the specified timerange"}
