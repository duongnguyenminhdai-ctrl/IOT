/*
 * ==============================================================================
 * Course Project: Hệ thống IoT giám sát và phát hiện xâm nhập trước cửa nhà
 * Node: Physical IoT Node (ESP32 DevKit V1 - 38 pins)
 * File: esp32_security_node.ino
 * ==============================================================================
 * Pinout Configuration:
 *  - MC-38 Magnetic Door Sensor : GPIO 14 (INPUT_PULLUP + Interrupt CHANGE)
 *  - PIR HC-SR501 Motion Sensor : GPIO 13 (INPUT)
 *  - OLED 0.96" I2C (SSD1306)    : SDA -> GPIO 21, SCL -> GPIO 22
 *  - Active Buzzer (5V)         : GPIO 27 (OUTPUT)
 *  - Relay Module (5V 1-CH)     : GPIO 26 (OUTPUT)
 *  - Status LED Green (Armed)   : GPIO 4  (OUTPUT)
 *  - Status LED Red (Alarm)     : GPIO 2  (OUTPUT)
 *  - Emergency Panic Button     : GPIO 15 (INPUT_PULLUP)
 *
 * MQTT Topics Contract:
 *  - Publish:
 *      home/sensor/door  -> "OPEN" / "CLOSED"
 *      home/sensor/pir   -> "MOTION" / "STILL"
 *  - Subscribe:
 *      home/actuator/alarm -> "ON" / "OFF" or {"alarm":"ON"/"OFF"}
 *      home/system/mode    -> "ARMED" / "DISARMED"
 * ==============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ---------------------- PIN DEFINITIONS ----------------------
#define PIN_DOOR_SENSOR     14    // MC-38 Magnetic Sensor (Pull-up)
#define PIN_PIR_SENSOR      13    // HC-SR501 Motion Sensor
#define PIN_BUZZER          27    // Active 5V Buzzer
#define PIN_RELAY           26    // 1-channel Relay (Active LOW / HIGH)
#define PIN_LED_GREEN       4     // System Armed Indicator
#define PIN_LED_RED         2     // Alarm Triggered Indicator
#define PIN_EMERGENCY_BTN   15    // Emergency Panic Button (Pull-up)

// Relay active level (Most standard 5V relay modules are active LOW)
#define RELAY_ACTIVE_LEVEL  LOW
#define RELAY_INACTIVE_LEVEL HIGH

// ---------------------- OLED DISPLAY SETUP -------------------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
#define SCREEN_ADDRESS 0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ---------------------- NETWORK CONFIGURATION ----------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const char* MQTT_SERVER   = "192.168.1.100";  // Laptop Edge IP running Mosquitto
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "";               // Leave empty if no authentication
const char* MQTT_PASS     = "";
const char* CLIENT_ID     = "ESP32_Security_Node";

// MQTT Topics
const char* TOPIC_SENSOR_DOOR     = "home/sensor/door";
const char* TOPIC_SENSOR_PIR      = "home/sensor/pir";
const char* TOPIC_ACTUATOR_ALARM  = "home/actuator/alarm";
const char* TOPIC_SYSTEM_MODE     = "home/system/mode";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ---------------------- SYSTEM STATES & TIMERS ---------------
volatile bool doorStateChanged = false;
volatile int  lastDoorRawState = HIGH;

bool isArmed        = true;   // Default ARMED on boot
bool isAlarmActive  = false;
String currentDoor  = "CLOSED";
String currentPIR   = "STILL";
unsigned int alarmCount = 0;

// Non-blocking millisecond timers
unsigned long lastDisplayUpdate = 0;
const unsigned long DISPLAY_INTERVAL = 1000; // 1s refresh rate

unsigned long lastPirCheck = 0;
const unsigned long PIR_INTERVAL = 250;      // 250ms check rate

unsigned long lastMqttReconnect = 0;
const unsigned long MQTT_RECONNECT_INTERVAL = 5000;

unsigned long lastBuzzerToggle = 0;
bool buzzerBeepState = false;

// Button debounce
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// ---------------------- HARDWARE INTERRUPT (MC-38) -----------
// MC-38: Cửa đóng -> 2 cực nam châm gần nhau -> Tiếp điểm đóng (GND) -> Pin đọc LOW.
// Cửa mở -> Tiếp điểm hở -> Kéo lên PULLUP -> Pin đọc HIGH.
void IRAM_ATTR handleDoorInterrupt() {
  doorStateChanged = true;
}

// ---------------------- HARDWARE ACTUATOR HELPERS ------------
void setAlarmOutputs(bool active) {
  isAlarmActive = active;
  if (!active) {
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_RELAY, RELAY_INACTIVE_LEVEL);
    digitalWrite(PIN_LED_RED, LOW);
  } else {
    digitalWrite(PIN_RELAY, RELAY_ACTIVE_LEVEL);
    digitalWrite(PIN_LED_RED, HIGH);
  }
}

// ---------------------- OLED DISPLAY FUNCTION ----------------
void updateOLED() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  // Line 1: Header / Mode
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("MODE: ");
  if (isArmed) {
    display.print("[ARMED]");
  } else {
    display.print("[DISARMED]");
  }

  // Line 2: IP Address
  display.setCursor(0, 13);
  display.print("IP: ");
  display.print(WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : "No WiFi");

  // Line 3: MQTT Status
  display.setCursor(0, 25);
  display.print("MQTT: ");
  display.print(mqttClient.connected() ? "ONLINE" : "OFFLINE");

  // Line 4: Door & PIR Status
  display.setCursor(0, 37);
  display.print("D: ");
  display.print(currentDoor);
  display.print(" | PIR: ");
  display.print(currentPIR);

  // Line 5: Alarm Status & Counter
  display.setCursor(0, 50);
  if (isAlarmActive) {
    display.print("! ALARM TRIGGERED !");
  } else {
    display.print("Alarms: ");
    display.print(alarmCount);
  }

  display.display();
}

// ---------------------- MQTT CALLBACK ------------------------
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();

  Serial.print("[MQTT RX] ");
  Serial.print(topic);
  Serial.print(" : ");
  Serial.println(message);

  // Topic: home/actuator/alarm
  if (String(topic) == TOPIC_ACTUATOR_ALARM) {
    if (message.indexOf("ON") >= 0) {
      if (!isAlarmActive) {
        alarmCount++;
      }
      setAlarmOutputs(true);
    } else if (message.indexOf("OFF") >= 0) {
      setAlarmOutputs(false);
    }
  }
  // Topic: home/system/mode
  else if (String(topic) == TOPIC_SYSTEM_MODE) {
    if (message == "ARMED") {
      isArmed = true;
      digitalWrite(PIN_LED_GREEN, HIGH);
    } else if (message == "DISARMED") {
      isArmed = false;
      digitalWrite(PIN_LED_GREEN, LOW);
      setAlarmOutputs(false); // Auto disarm alarm
    }
  }

  updateOLED();
}

// ---------------------- RECONNECT MQTT -----------------------
void reconnectMQTT() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  if (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection to ");
    Serial.print(MQTT_SERVER);
    Serial.print("...");

    if (mqttClient.connect(CLIENT_ID, MQTT_USER, MQTT_PASS)) {
      Serial.println(" CONNECTED!");
      mqttClient.subscribe(TOPIC_ACTUATOR_ALARM);
      mqttClient.subscribe(TOPIC_SYSTEM_MODE);
      
      // Publish initial state upon connection
      mqttClient.publish(TOPIC_SENSOR_DOOR, currentDoor.c_str(), true);
      mqttClient.publish(TOPIC_SENSOR_PIR, currentPIR.c_str(), true);
    } else {
      Serial.print(" FAILED, rc=");
      Serial.println(mqttClient.state());
    }
  }
}

// ---------------------- SETUP --------------------------------
void setup() {
  Serial.begin(115200);
  delay(100);

  // Initialize GPIO Modes
  pinMode(PIN_DOOR_SENSOR, INPUT_PULLUP);
  pinMode(PIN_PIR_SENSOR, INPUT);
  pinMode(PIN_EMERGENCY_BTN, INPUT_PULLUP);

  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);

  // Default Pin States
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_RELAY, RELAY_INACTIVE_LEVEL);
  digitalWrite(PIN_LED_GREEN, isArmed ? HIGH : LOW);
  digitalWrite(PIN_LED_RED, LOW);

  // I2C OLED Initialization
  Wire.begin(21, 22);
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed. Check I2C wiring (SDA=21, SCL=22)."));
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 20);
    display.println("ESP32 SECURITY NODE");
    display.setCursor(20, 35);
    display.println("Connecting WiFi...");
    display.display();
  }

  // WiFi Connection
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  int wifiAttempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < 30) {
    delay(300);
    Serial.print(".");
    wifiAttempts++;
  }
  Serial.println("");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi Connected! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi Connection Timeout. Running in offline/reconnect loop.");
  }

  // MQTT Client
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  // Initial read of Door Sensor
  lastDoorRawState = digitalRead(PIN_DOOR_SENSOR);
  currentDoor = (lastDoorRawState == LOW) ? "CLOSED" : "OPEN";

  // Attach Hardware Interrupt for MC-38
  attachInterrupt(digitalPinToInterrupt(PIN_DOOR_SENSOR), handleDoorInterrupt, CHANGE);

  updateOLED();
}

// ---------------------- LOOP (STRICTLY NON-BLOCKING) ---------
void loop() {
  unsigned long currentMillis = millis();

  // 1. Maintain MQTT Client Loop
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttClient.connected()) {
      if (currentMillis - lastMqttReconnect >= MQTT_RECONNECT_INTERVAL) {
        lastMqttReconnect = currentMillis;
        reconnectMQTT();
      }
    } else {
      mqttClient.loop();
    }
  }

  // 2. Process Door Sensor Interrupt Flag
  if (doorStateChanged) {
    doorStateChanged = false;
    int rawState = digitalRead(PIN_DOOR_SENSOR);
    lastDoorRawState = rawState;
    String newDoorState = (rawState == LOW) ? "CLOSED" : "OPEN";

    if (newDoorState != currentDoor) {
      currentDoor = newDoorState;
      Serial.print("[DOOR STATUS CHANGED] -> ");
      Serial.println(currentDoor);

      if (mqttClient.connected()) {
        mqttClient.publish(TOPIC_SENSOR_DOOR, currentDoor.c_str(), true);
      }

      // If Door OPENS while system is ARMED -> Local hardware reaction immediately!
      if (currentDoor == "OPEN" && isArmed) {
        alarmCount++;
        setAlarmOutputs(true);
        if (mqttClient.connected()) {
          mqttClient.publish(TOPIC_ACTUATOR_ALARM, "{\"alarm\":\"ON\"}", false);
        }
      }
      updateOLED();
    }
  }

  // 3. Sample PIR Motion Sensor (Every 250ms)
  if (currentMillis - lastPirCheck >= PIR_INTERVAL) {
    lastPirCheck = currentMillis;
    int pirReading = digitalRead(PIN_PIR_SENSOR);
    String newPirState = (pirReading == HIGH) ? "MOTION" : "STILL";

    if (newPirState != currentPIR) {
      currentPIR = newPirState;
      Serial.print("[PIR STATUS CHANGED] -> ");
      Serial.println(currentPIR);

      if (mqttClient.connected()) {
        mqttClient.publish(TOPIC_SENSOR_PIR, currentPIR.c_str(), true);
      }
      updateOLED();
    }
  }

  // 4. Handle Emergency Panic Button (Active LOW with debounce)
  int reading = digitalRead(PIN_EMERGENCY_BTN);
  if (reading != lastButtonState) {
    lastDebounceTime = currentMillis;
  }
  if ((currentMillis - lastDebounceTime) > DEBOUNCE_DELAY) {
    if (reading == LOW && lastButtonState == HIGH) {
      Serial.println("[EMERGENCY] Panic Button Pressed!");
      alarmCount++;
      setAlarmOutputs(true);
      if (mqttClient.connected()) {
        mqttClient.publish(TOPIC_ACTUATOR_ALARM, "{\"alarm\":\"ON\",\"reason\":\"PANIC_BUTTON\"}", false);
      }
      updateOLED();
    }
  }
  lastButtonState = reading;

  // 5. Pulsing Sound for Active Alarm (Beep pattern without delay)
  if (isAlarmActive) {
    if (currentMillis - lastBuzzerToggle >= 300) {
      lastBuzzerToggle = currentMillis;
      buzzerBeepState = !buzzerBeepState;
      digitalWrite(PIN_BUZZER, buzzerBeepState ? HIGH : LOW);
    }
  }

  // 6. Update OLED Display Periodically (Every 1 second)
  if (currentMillis - lastDisplayUpdate >= DISPLAY_INTERVAL) {
    lastDisplayUpdate = currentMillis;
    updateOLED();
  }
}

