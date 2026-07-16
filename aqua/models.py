#aqua.evolv
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from aqua.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password = Column(String(120), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, default=False)


class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    temperature = Column(Float, nullable=False)
    oxygen = Column(Float, nullable=False)


