from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DeviceState
from app.mqtt_client import mqtt_manager

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/status")
def get_system_status():
    """Returns real-time states of sensors and actuators."""
    return {
        "is_armed": mqtt_manager.is_armed,
        "alarm_active": mqtt_manager.alarm_active,
        "door_state": mqtt_manager.door_status,
        "pir_state": mqtt_manager.pir_status,
        "mqtt_connected": mqtt_manager.is_connected
    }

@router.post("/arm")
def arm_system():
    """Sets system into ARMED mode."""
    mqtt_manager.publish_mode(armed=True)
    return {"status": "success", "mode": "ARMED"}

@router.post("/disarm")
def disarm_system():
    """Disarms system and silences any active alarm."""
    mqtt_manager.publish_mode(armed=False)
    mqtt_manager.publish_alarm("OFF")
    return {"status": "success", "mode": "DISARMED"}

@router.post("/mute-alarm")
def mute_alarm():
    """Mutes the active alarm buzzer and relay."""
    mqtt_manager.publish_alarm("OFF")
    return {"status": "success", "alarm": "OFF"}

@router.post("/trigger-alarm")
def manual_trigger_alarm():
    """Manually sounds the alarm."""
    mqtt_manager.trigger_alarm(
        event_type="MANUAL_ALARM",
        description="Báo động được kích hoạt thủ công từ Dashboard!"
    )
    return {"status": "success", "alarm": "ON"}

