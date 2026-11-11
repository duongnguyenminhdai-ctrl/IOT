import json
import logging
import threading
import time
from datetime import datetime
import paho.mqtt.client as mqtt
from app.config import settings
from app.database import SessionLocal
from app.models import Incident, DeviceState
from app.telegram_notifier import telegram_notifier

logger = logging.getLogger("mqtt_client")

class MQTTManager:
    def __init__(self):
        self.client = mqtt.Client(client_id="fastapi_edge_server", clean_session=True)
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.is_connected = False
        self.door_status = "CLOSED"
        self.pir_status = "STILL"
        self.is_armed = True
        self.alarm_active = False
        self._lock = threading.Lock()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            logger.info("Successfully connected to MQTT Broker.")
            client.subscribe(settings.TOPIC_SENSOR_DOOR)
            client.subscribe(settings.TOPIC_SENSOR_PIR)
            client.subscribe(settings.TOPIC_ACTUATOR_ALARM)
            client.subscribe(settings.TOPIC_SYSTEM_MODE)
            
            # Sync initial armed mode to broker
            self.publish_mode(self.is_armed)
        else:
            logger.error(f"MQTT Connection failed with return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        logger.warning(f"MQTT Disconnected (rc={rc}). Reconnecting will be attempted.")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_raw = msg.payload.decode("utf-8").strip()
        logger.info(f"MQTT RX [{topic}]: {payload_raw}")

        try:
            # Handle Door Sensor
            if topic == settings.TOPIC_SENSOR_DOOR:
                self.door_status = payload_raw.upper()
                self._update_db_state()
                if self.door_status == "OPEN" and self.is_armed:
                    self.trigger_alarm(event_type="DOOR_BREACH", description="Cửa chính bị mở khi đang kích hoạt báo động!")

            # Handle PIR Motion
            elif topic == settings.TOPIC_SENSOR_PIR:
                self.pir_status = payload_raw.upper()
                self._update_db_state()
                if self.pir_status == "MOTION" and self.is_armed:
                    logger.info("PIR detected motion outside the door.")

            # Handle System Mode
            elif topic == settings.TOPIC_SYSTEM_MODE:
                self.is_armed = (payload_raw.upper() == "ARMED")
                self._update_db_state()

            # Handle Actuator Alarm
            elif topic == settings.TOPIC_ACTUATOR_ALARM:
                # payload can be "ON"/"OFF" or json {"alarm": "ON"}
                state = payload_raw.upper()
                if "ON" in state:
                    self.alarm_active = True
                elif "OFF" in state:
                    self.alarm_active = False
                self._update_db_state()

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _update_db_state(self):
        try:
            db = SessionLocal()
            state = db.query(DeviceState).filter(DeviceState.id == 1).first()
            if not state:
                state = DeviceState(
                    id=1,
                    is_armed=self.is_armed,
                    is_alarm_active=self.alarm_active,
                    door_state=self.door_status,
                    pir_state=self.pir_status
                )
                db.add(state)
            else:
                state.is_armed = self.is_armed
                state.is_alarm_active = self.alarm_active
                state.door_state = self.door_status
                state.pir_state = self.pir_status
                state.updated_at = datetime.utcnow()
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to update device state in DB: {e}")

    def trigger_alarm(self, event_type: str, description: str, snapshot_path: str = None, person_id: int = None, dwell_time: float = None):
        with self._lock:
            self.alarm_active = True
            self.publish_alarm("ON")

            # Persist Incident in DB
            try:
                db = SessionLocal()
                incident = Incident(
                    event_type=event_type,
                    description=description,
                    snapshot_path=snapshot_path,
                    person_id=person_id,
                    dwell_time=dwell_time,
                    timestamp=datetime.utcnow()
                )
                db.add(incident)
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"DB Error logging incident: {e}")

            # Send Telegram Alert
            alert_text = (
                f"🚨 <b>CẢNH BÁO AN NINH!</b> 🚨\n\n"
                f"⚠️ <b>Sự kiện:</b> {event_type}\n"
                f"📝 <b>Chi tiết:</b> {description}\n"
                f"🕒 <b>Thời gian:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            if dwell_time:
                alert_text += f"⏱️ <b>Thời gian lảng vảng:</b> {dwell_time:.1f}s\n"

            telegram_notifier.send_alert(alert_text, snapshot_path)

    def publish_alarm(self, state: str):
        payload = json.dumps({"alarm": state.upper()})
        self.client.publish(settings.TOPIC_ACTUATOR_ALARM, payload, qos=1)
        self.alarm_active = (state.upper() == "ON")
        self._update_db_state()
        logger.info(f"Published alarm state: {payload}")

    def publish_mode(self, armed: bool):
        mode_str = "ARMED" if armed else "DISARMED"
        self.client.publish(settings.TOPIC_SYSTEM_MODE, mode_str, qos=1, retain=True)
        self.is_armed = armed
        self._update_db_state()
        logger.info(f"Published system mode: {mode_str}")

    def start(self):
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT loop started.")
        except Exception as e:
            logger.warning(f"Could not connect to MQTT Broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT} - {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT loop stopped.")

mqtt_manager = MQTTManager()

