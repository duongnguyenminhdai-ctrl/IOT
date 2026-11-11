# Hệ Thống IoT Giám Sát và Phát Hiện Xâm Nhập Trước Cửa Nhà Dựa Trên Phân Tích Hành Vi Bất Thường

Dự án áp dụng mô hình **Hybrid Edge-IoT Architecture**:
- **Edge AI Server (Laptop/PC):** Chạy Windows, thực thi FastAPI Backend, OpenCV thu nhận hình ảnh từ USB Webcam, YOLOv8n + ByteTrack nhận diện người và tính dwell time trong vùng ROI trước cửa, lưu trữ sự cố SQLite và phân phối cảnh báo qua Telegram Bot và Mosquitto MQTT Broker.
- **Physical IoT Peripheral Node (ESP32 DevKit V1 - 38 pins):** Giám sát cảm biến cửa từ MC-38 (phần cứng ngắt interrupt), cảm biến chuyển động PIR HC-SR501, nút nhấn khẩn cấp, hiển thị OLED SSD1306 và điều khiển còi hú Buzzer 5V, Module Rơ-le 5V.
- **Frontend Dashboard (React 18 + Vite + TailwindCSS):** Hiển thị luồng video Edge AI thời gian thực, bảng trạng thái thiết bị, nút bấm điều khiển tức thời và lịch sử cảnh báo có ảnh bằng chứng.

---

## 1. Sơ Đồ Đấu Nối Phần Cứng (ESP32 Pinout)

| Linh kiện | Chân trên linh kiện | Chân trên ESP32 DevKit V1 (38 pins) | Chế độ cấu hình | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **Cảm biến cửa từ MC-38** | Dây 1<br>Dây 2 | **GPIO 14**<br>**GND** | `INPUT_PULLUP` + Interrupt `CHANGE` | Đóng cửa: LOW, Mở cửa: HIGH |
| **Cảm biến PIR HC-SR501** | VCC<br>OUT<br>GND | **5V (VIN)**<br>**GPIO 13**<br>**GND** | `INPUT` | Phát hiện thân nhiệt chuyển động |
| **Màn hình OLED 0.96" SSD1306** | VCC<br>GND<br>SCL<br>SDA | **3V3 hoặc 5V**<br>**GND**<br>**GPIO 22**<br>**GPIO 21** | I2C Hardware Bus (0x3C) | Hiển thị IP, MQTT, Mode, Đếm báo động |
| **Active Buzzer 5V** | VCC (+)<br>GND (-) | **GPIO 27**<br>**GND** | `OUTPUT` | Còi hú xung khi có báo động |
| **Module Rơ-le 5V 1 Kênh** | VCC<br>GND<br>IN | **5V (VIN)**<br>**GND**<br>**GPIO 26** | `OUTPUT` | Kích đèn phụ / khóa chốt (Active LOW) |
| **Nút bấm khẩn cấp (Panic)** | Chân 1<br>Chân 2 | **GPIO 15**<br>**GND** | `INPUT_PULLUP` | Nhấn giữ để kích hoạt báo động ngay |
| **LED Trạng thái Xanh (Armed)** | Anode (+)<br>Cathode (-) | **GPIO 4** (qua trở 220Ω)<br>**GND** | `OUTPUT` | Sáng khi hệ thống bật ARMED |
| **LED Trạng thái Đỏ (Alarm)** | Anode (+)<br>Cathode (-) | **GPIO 2** (qua trở 220Ω)<br>**GND** | `OUTPUT` | Sáng/nhấp nháy khi báo động |

---

## 2. Giao Thức MQTT Topics Contract

| Topic | Hướng | Dữ liệu mẫu | Mục đích |
| :--- | :--- | :--- | :--- |
| `home/sensor/door` | ESP32 &rarr; Server | `"OPEN"` hoặc `"CLOSED"` | Báo trạng thái tiếp điểm cửa từ MC-38 |
| `home/sensor/pir` | ESP32 &rarr; Server | `"MOTION"` hoặc `"STILL"` | Báo chuyển động từ cảm biến PIR |
| `home/actuator/alarm` | 2 chiều | `{"alarm": "ON"}` hoặc `{"alarm": "OFF"}` | Điều khiển kích hoạt còi hú/rơ-le |
| `home/system/mode` | 2 chiều | `"ARMED"` hoặc `"DISARMED"` | Bật/tắt chế độ phòng vệ an ninh |

---

## 3. Cấu Trúc Thư Mục Dự Án

```
camera_an_ninh/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── stream.py            # MJPEG stream & cấu hình ROI
│   │   │   ├── incidents.py         # Lịch sử sự cố & snapshot preview
│   │   │   └── system.py            # API Arm/Disarm, Mute Alarm
│   │   ├── services/
│   │   │   ├── camera_stream.py     # Threaded non-blocking USB Webcam grabber
│   │   │   └── loitering_engine.py  # YOLOv8n + ByteTrack + ROI Polygon + Loitering Timer
│   │   ├── config.py                # Pydantic Settings
│   │   ├── database.py              # SQLite & SQLAlchemy engine
│   │   ├── models.py                # Bảng cơ sở dữ liệu Incident & DeviceState
│   │   ├── mqtt_client.py           # Quản lý MQTT subscribe/publish
│   │   ├── telegram_notifier.py     # Gửi tin nhắn & ảnh bằng chứng qua Telegram Bot
│   │   └── main.py                  # Điểm khởi động FastAPI
│   ├── data/
│   │   └── snapshots/               # Thư mục lưu ảnh chụp bằng chứng khi có sự cố
│   ├── requirements.txt
│   └── .env.example
├── firmware/
│   └── esp32_security_node/
│       └── esp32_security_node.ino  # Mã nguồn C++ hoàn chỉnh cho ESP32 DevKit V1
└── dashboard/
    ├── src/
    │   ├── components/
    │   │   ├── LiveFeed.jsx         # Video stream thời gian thực
    │   │   ├── DeviceStatus.jsx     # Thẻ hiển thị trạng thái phần cứng
    │   │   ├── QuickActions.jsx     # Các nút thao tác nhanh
    │   │   └── IncidentLogs.jsx     # Bảng nhật ký sự cố & modal xem ảnh
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## 4. Hướng Dẫn Cài Đặt & Chạy Hệ Thống

### Bước 1: Khởi động Mosquitto MQTT Broker
Nếu đã cài Mosquitto trên Windows:
```powershell
# Chạy Mosquitto broker trên cổng mặc định 1883
mosquitto -v
```

### Bước 2: Nạp Firmware cho ESP32 DevKit V1
1. Mở file `firmware/esp32_security_node/esp32_security_node.ino` bằng Arduino IDE.
2. Cài đặt các thư viện trong Library Manager:
   - `PubSubClient` (bởi Nick O'Leary)
   - `Adafruit SSD1306` & `Adafruit GFX Library`
3. Cập nhật thông số mạng:
   ```cpp
   const char* WIFI_SSID     = "Tên_WiFi_Của_Bạn";
   const char* WIFI_PASSWORD = "Mật_Khẩu_WiFi";
   const char* MQTT_SERVER   = "192.168.1.xxx"; // Địa chỉ IP LAN của Laptop chạy Mosquitto
   ```
4. Chọn Board: **ESP32 Dev Module** (hoặc ESP32 DevKit V1), cắm cáp micro USB và nhấn **Upload**.

### Bước 3: Cài đặt và chạy Backend (FastAPI + YOLOv8)
```powershell
cd d:\aKTS\IOT\camera_an_ninh\backend

# Tạo môi trường ảo Python
python -m venv venv
.\venv\Scripts\activate

# Cài đặt thư viện
pip install -r requirements.txt

# Cấu hình biến môi trường (nếu muốn dùng Telegram)
copy .env.example .env

# Khởi chạy server FastAPI (cổng 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Bước 4: Cài đặt và chạy Dashboard (React + Vite)
Mở cửa sổ terminal mới:
```powershell
cd d:\aKTS\IOT\camera_an_ninh\dashboard

# Cài đặt node_modules
npm install

# Khởi chạy Frontend dev server
npm run dev
```
Truy cập giao diện tại: `http://localhost:5173`

