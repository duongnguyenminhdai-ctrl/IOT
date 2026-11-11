import os
from pydantic_settings import BaseSettings
from typing import List, Tuple

class Settings(BaseSettings):
    APP_NAME: str = "IoT Door Intrusion & Loitering Detection System"
    VERSION: str = "1.0.0"
    
    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    
    # MQTT Topics
    TOPIC_SENSOR_DOOR: str = "home/sensor/door"
    TOPIC_SENSOR_PIR: str = "home/sensor/pir"
    TOPIC_ACTUATOR_ALARM: str = "home/actuator/alarm"
    TOPIC_SYSTEM_MODE: str = "home/system/mode"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_ENABLED: bool = False
    
    # Camera & Vision
    CAMERA_INDEX: int = 0
    FRAME_WIDTH: int = 1280
    FRAME_HEIGHT: int = 720
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    
    # Loitering Rule
    LOITERING_THRESHOLD_SECONDS: float = 20.0
    ALARM_COOLDOWN_SECONDS: float = 30.0
    
    # Default ROI Polygon points (normalized percentages [x, y] from 0.0 to 1.0)
    # Can be adjusted via settings or dynamically
    DEFAULT_ROI_PERCENT: List[Tuple[float, float]] = [
        (0.20, 0.25),
        (0.80, 0.25),
        (0.90, 0.95),
        (0.10, 0.95)
    ]
    
    # Storage
    DATABASE_URL: str = "sqlite:///./data/security_system.db"
    SNAPSHOT_DIR: str = "./data/snapshots"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

