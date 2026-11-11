from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from app.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # LOITERING, DOOR_BREACH, PIR_MOTION, MANUAL_ALARM
    description = Column(String(255), nullable=True)
    snapshot_path = Column(String(255), nullable=True)
    person_id = Column(Integer, nullable=True)
    dwell_time = Column(Float, nullable=True)

class DeviceState(Base):
    __tablename__ = "device_states"

    id = Column(Integer, primary_key=True, default=1)
    is_armed = Column(Boolean, default=True)
    is_alarm_active = Column(Boolean, default=False)
    door_state = Column(String(20), default="CLOSED")    # OPEN, CLOSED
    pir_state = Column(String(20), default="STILL")       # MOTION, STILL
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

