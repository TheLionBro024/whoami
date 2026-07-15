import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aqua.database import get_db
from aqua.models import SensorData, User
from aqua.security import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("")
async def export_data(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    resolution: str = Query(..., description="raw, hourly, daily_morning_evening"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time")
        
    result = await db.execute(
        select(SensorData)
        .where(SensorData.timestamp >= start_time)
        .where(SensorData.timestamp <= end_time)
        .order_by(SensorData.timestamp.asc())
    )
    data = result.scalars().all()
    
    if not data:
        raise HTTPException(status_code=404, detail="No data found in the specified timerange")
        
    # Convert to pandas DataFrame
    df = pd.DataFrame([{
        "Timestamp": d.timestamp,
        "Temperature": d.temperature,
        "Oxygen": d.oxygen
    } for d in data])
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df.set_index('Timestamp', inplace=True)
    
    if resolution == "hourly":
        df = df.resample('H').mean().dropna()
    elif resolution == "daily_morning_evening":
        # Group by date, and get mean for morning (0-12) and evening (12-24)
        morning_mask = df.index.hour < 12
        evening_mask = df.index.hour >= 12
        
        df_morning = df[morning_mask].resample('D').mean()
        df_evening = df[evening_mask].resample('D').mean()
        
        df_morning['Period'] = 'Morning'
        df_evening['Period'] = 'Evening'
        
        df = pd.concat([df_morning, df_evening]).dropna().sort_index()
    elif resolution == "raw":
        pass # keep as is
    else:
        raise HTTPException(status_code=400, detail="Invalid resolution")
        
    # Generate Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sensor Data')
    output.seek(0)
    
    filename = f"sensor_data_{resolution}_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.xlsx"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
