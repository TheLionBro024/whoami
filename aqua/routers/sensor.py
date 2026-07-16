#aqua.evolv
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from aqua.database import get_db
from aqua.models import SensorData
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aqua.routers.settings import load_settings

# Load API key from aqua/.env.aqua
_AQUA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(_AQUA_DIR, ".env.aqua"))
AQUA_API_KEY = os.getenv("AQUA_API_KEY", "Evolv.IoTBerglund2026")

router = APIRouter(prefix="/api/sensor_data", tags=["sensor"])

class SensorDataInput(BaseModel):
    temperature: Optional[float] = None
    oxygen: Optional[float] = None

@router.get("")
async def get_sensor_data(time_range: str = "hour", db: AsyncSession = Depends(get_db)):
    # All timestamps in DB are UTC (datetime.utcnow).
    now_utc = datetime.utcnow()
    
    if time_range == "hour":
        start_time = now_utc - timedelta(hours=1)
        result = await db.execute(select(SensorData).where(SensorData.timestamp >= start_time).order_by(SensorData.timestamp.asc()))
        data = result.scalars().all()
    elif time_range == "day":
        start_time = now_utc - timedelta(hours=24)
        result = await db.execute(select(SensorData).where(SensorData.timestamp >= start_time).order_by(SensorData.timestamp.asc()))
        data = result.scalars().all()
    elif time_range == "week" or time_range == "month":
        days = 7 if time_range == "week" else 30
        start_time = now_utc - timedelta(days=days)
        
        # SQLite doesn't natively do timezone-aware date truncation easily, but we can group by date string
        # func.date() works on SQLite datetime columns
        result = await db.execute(
            select(
                func.date(SensorData.timestamp).label('day'),
                func.avg(SensorData.temperature).label('avg_temp'),
                func.avg(SensorData.oxygen).label('avg_oxy')
            )
            .where(SensorData.timestamp >= start_time)
            .group_by(func.date(SensorData.timestamp))
            .order_by(func.date(SensorData.timestamp).asc())
        )
        data = result.all()
        
        return [
            {
                # For daily averages, just return the date
                "timestamp": d.day,
                "temperature": round(d.avg_temp, 2) if d.avg_temp else 0,
                "oxygen": round(d.avg_oxy, 2) if d.avg_oxy else 0
            }
            for d in data
        ]
    else:
        # Default fallback to 50 latest
        result = await db.execute(select(SensorData).order_by(SensorData.timestamp.desc()).limit(50))
        data = result.scalars().all()
        data.reverse()

    # For hour/day/default ranges (raw data), adjust to UTC-3
    formatted_data = []
    for d in data:
        # UTC to UTC-3
        local_time = d.timestamp - timedelta(hours=3)
        formatted_data.append({
            "timestamp": local_time.strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": d.temperature,
            "oxygen": d.oxygen
        })
        
    return formatted_data

@router.post("/add")
async def add_sensor_data(
    req: SensorDataInput, 
    x_api_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if x_api_key != AQUA_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid API Key.")

    if req.temperature is None and req.oxygen is None:
        raise HTTPException(status_code=400, detail="Missing temperature or oxygen")
        
    result = await db.execute(select(SensorData).order_by(SensorData.timestamp.desc()).limit(1))
    latest = result.scalars().first()
    
    final_temp = float(req.temperature) if req.temperature is not None else (latest.temperature if latest else 0.0)
    final_oxy = float(req.oxygen) if req.oxygen is not None else (latest.oxygen if latest else 0.0)
    
    new_data = SensorData(temperature=final_temp, oxygen=final_oxy)
    db.add(new_data)
    await db.commit()
    
    # Return debug_mode from settings so the ESP32 can update its state immediately
    settings = load_settings()
    return {
        "status": "success",
        "message": "Sensor data added successfully",
        "debug_mode": settings.get("debug_mode", False)
    }
