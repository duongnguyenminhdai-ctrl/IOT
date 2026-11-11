# TỔNG DANH SÁCH LINH KIỆN CẦN MUA & DỤNG CỤ MÔ HÌNH
**Đồ án:** Hệ thống IoT giám sát và phát hiện xâm nhập trước cửa nhà dựa trên phân tích hành vi bất thường  
**Bo mạch trung tâm:** ESP32 DevKit V1 (38 chân) + Edge AI Server (Laptop)

---

## I. BẢNG DANH SÁCH LINH KIỆN ĐIỆN TỬ CẦN MUA

| STT | Tên linh kiện | Thông số kỹ thuật / Phân loại | Số lượng | Giá tham khảo (VNĐ) | Mục đích sử dụng |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Bo mạch ESP32 DevKit V1** | **Bản 38 chân** (ESP-WROOM-32), WiFi + BLE, nạp qua cổng Micro-USB | **1 cái** | ~75.000 - 95.000 | Bộ vi điều khiển trung tâm IoT |
| **2** | **Cảm biến cửa từ MC-38** | Dạng tiếp điểm thường đóng/hở nam châm (Reed switch), có sẵn dây dẫn | **1 bộ** | ~15.000 - 25.000 | Gắn vào khung và cánh cửa (GPIO 14 - Ngắt) |
| **3** | **Cảm biến chuyển động PIR HC-SR501** | Góc quét 120°, cự ly 3 - 7m, có 2 chiết áp chỉnh độ nhạy & thời gian | **1 cái** | ~20.000 - 30.000 | Phát hiện người tiếp cận vùng cửa (GPIO 13) |
| **4** | **Màn hình OLED 0.96 inch** | Chuẩn giao tiếp **I2C (4 chân: VCC, GND, SCL, SDA)**, chip SSD1306, 128x64 | **1 cái** | ~45.000 - 55.000 | Hiển thị IP, trạng thái MQTT, chế độ an ninh (GPIO 21, 22) |
| **5** | **Còi báo Active Buzzer 5V** | **Active Buzzer (Còi chíp)** - Cấp 5V tự kêu, không cần phát xung PWM | **1 cái** | ~5.000 - 10.000 | Phát âm thanh báo động khẩn cấp (GPIO 27) |
| **6** | **Module Relay 5V 1 Kênh** | Có cách ly quang (Optocoupler), tải 250VAC/10A hoặc 30VDC/10A (kích mức LOW) | **1 cái** | ~15.000 - 20.000 | Đóng ngắt đèn phụ / chốt khóa điện (GPIO 26) |
| **7** | **Nút nhấn 4 chân (Push Button)** | Nút nhấn nhả kích thước 12x12mm hoặc nút nhấn chuông cửa có nắp | **1 - 2 cái** | ~3.000 - 5.000 | Nút báo động khẩn cấp Panic tại cửa (GPIO 15) |
| **8** | **LED Đơn 5mm (Đỏ & Xanh lá)** | LED 5mm tiêu chuẩn (1 cái Đỏ + 1 cái Xanh) | **2 cái** | ~2.000 | LED Xanh (Armed - GPIO 4), LED Đỏ (Alarm - GPIO 2) |
| **9** | **Điện trở hạn dòng 220Ω (hoặc 330Ω)** | Công suất 1/4W | **2 - 4 con** | ~2.000 | Mắc nối tiếp bảo vệ 2 LED không bị cháy |
| **10**| **Test bo Breadboard (Bo cắm)** | Loại lớn MB-102 (830 lỗ) hoặc loại trung (400 lỗ) | **1 cái** | ~25.000 - 35.000 | Cắm bo mạch và dây test không cần hàn |
| **11**| **Bộ dây cắm Breadboard (Jumper Wires)** | Đủ 3 loại (dài 20cm):<br>- Đực - Đực (Male to Male)<br>- Đực - Cái (Male to Female)<br>- Cái - Cái (Female to Female) | **1 bó (mỗi loại 10-20 sợi)** | ~25.000 - 35.000 | Nối chân ESP32 ra các module cảm biến |
| **12**| **Cáp nạp Micro USB** | **Loại cáp truyền dữ liệu (Data Cable)**, chống nhiễu tốt | **1 sợi** | ~15.000 - 25.000 | Nạp code từ máy tính vào ESP32 và cấp nguồn |

---

## II. THIẾT BỊ PHẦN CỨNG SẴN CÓ / THIẾT BỊ ĐẦU CUỐI

| STT | Tên thiết bị | Yêu cầu cấu hình | Ghi chú |
| :---: | :--- | :--- | :--- |
| **1** | **Laptop / PC chạy Windows** | Core i5 trở lên, RAM tối thiểu 8GB, có cổng USB | Đóng vai trò **Edge AI Server** chạy Mosquitto Broker, FastAPI, YOLOv8 và React Dashboard. |
| **2** | **Webcam USB cắm ngoài** | Độ phân giải Full HD 1080p (hoặc 720p), kết nối USB 2.0/3.0 | Cắm trực tiếp vào laptop chiếu thẳng ra mô hình cửa để nhận diện AI. |
| **3** | **Bộ phát WiFi / 4G** | WiFi băng tần 2.4GHz (ESP32 chỉ hỗ trợ chuẩn 2.4GHz) | Phát từ điện thoại di động hoặc router phòng trọ để ESP32 và Laptop cùng vào 1 mạng LAN. |

---

## III. VẬT LIỆU TỰ LÀM SA BÀN / MÔ HÌNH CỬA DEMO

| STT | Vật liệu / Dụng cụ | Số lượng | Giá tham khảo (VNĐ) | Mục đích sử dụng |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Tấm bìa mô hình Fomex (dày 5mm)** | 1 tấm khổ A3 hoặc A2 | ~20.000 - 30.000 | Cắt làm khung tường và cánh cửa mô hình |
| **2** | **Bản lề kim loại mini (1 - 2cm)** | 1 - 2 cái | ~5.000 - 10.000 | Gắn vào mép để cánh cửa có thể đóng/mở thật |
| **3** | **Băng keo xốp 2 mặt / Keo nến** | 1 cuộn / 2 cây keo | ~10.000 - 15.000 | Dán cố định cảm biến MC-38, bo mạch lên mô hình |
| **4** | **Tuốc-nơ-vít dẹp 2mm nhỏ** | 1 cái | Nhà có sẵn | Dùng để xoay chỉnh 2 biến trở trên cảm biến PIR HC-SR501 |

---

## 💰 TỔNG KẾT CHI PHÍ DỰ KIẾN
* **Tổng tiền linh kiện điện tử:** $\approx$ **250.000 - 330.000 VNĐ** *(Chia cho 3 bạn $\approx$ 80.000 - 110.000 VNĐ/người)*.
* **Chi phí vật liệu làm mô hình cửa:** $\approx$ **40.000 - 50.000 VNĐ**.

---

## ⚠️ 4 LƯU Ý SỐNG CÒN KHI MUA LINH KIỆN (TRÁNH MUA NHẦM)

> [!WARNING]
> 1. **ESP32 phải chọn bản 38 chân:** Đừng mua nhầm bản ESP32 30 chân hay ESP8266 (ESP8266 rất yếu, không đủ chân và code này không chạy được).
> 2. **Còi báo (Buzzer):** Phải dặn người bán lấy đúng **Active Buzzer** (còi chủ động cấp nguồn 5V là tự kêu). Nếu mua nhầm *Passive Buzzer* (còi bị động) thì cấp 5V nó chỉ phát tiếng "tách" nhỏ mà không kêu liên tục được.
> 3. **Màn hình OLED 0.96":** Phải chọn loại **giao tiếp I2C 4 chân** (`VCC`, `GND`, `SCL`, `SDA`). Không mua loại SPI 7 chân vì sơ đồ code dự án đang sử dụng bus I2C chân 21 và 22.
> 4. **Cáp nạp Micro-USB:** Phải chắc chắn là cáp **truyền được dữ liệu (Data cable)**. Nhiều loại cáp sạc giá rẻ chỉ có 2 dây nguồn bên trong sẽ không thể nạp code vào ESP32 được và máy tính sẽ không nhận cổng COM.

---

## 🛒 ĐỊA ĐIỂM GỢI Ý MUA HÀNG NHANH
- **Đặt Online:** Shopee / Lazada (Gõ đúng từ khoá trong bảng, chọn shop cùng tỉnh/thành phố để ship nhanh 1-2 ngày).
- **Mua trực tiếp tại TP.HCM:**
  * Chợ Nhật Tảo (Quận 10)
  * Cửa hàng Điện tử NShop (Tân Phú / Quận 9)
  * Cửa hàng Banlinhkien / Thế Giới IC
- **Mua trực tiếp tại Hà Nội:**
  * Phố Lương Thế Vinh / Chợ Trời (Trần Cao Vân)
  * Linh Kiện Cầu Giấy / Banlinhkien
