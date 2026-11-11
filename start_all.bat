@echo off
TITLE He Thong IoT Giam Sat Cua & Bao Dong
COLOR 0A

echo ====================================================================
echo   KHOI DONG HE THONG IOT GIAM SAT CUA & HANH VI BAT THUONG (EDGE AI)
echo ====================================================================
echo.

:: 1. Kiem tra va khoi dong Mosquitto
echo [1/3] Dang khoi dong Mosquitto MQTT Broker...
start "Mosquitto MQTT Broker" cmd /k "mosquitto -v || echo [!] Khong tim thay mosquitto trong PATH. Vui long cai dat Mosquitto hoac chay thu cong."

timeout /t 2 /nobreak >nul

:: 2. Khoi dong Backend FastAPI
echo [2/3] Dang khoi dong Edge AI Backend (FastAPI + YOLOv8)...
start "FastAPI Edge Server" cmd /k "cd backend && (if not exist venv (python -m venv venv && call venv\Scripts\activate && pip install -r requirements.txt) else (call venv\Scripts\activate)) && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

:: 3. Khoi dong Frontend Dashboard
echo [3/3] Dang khoi dong React Dashboard (Vite)...
start "Vite React Dashboard" cmd /k "cd dashboard && npm run dev"

echo.
echo ====================================================================
echo   HE THONG DA DUOC KHOI DONG HOAN TAT!
echo   - Backend API: http://localhost:8000
echo   - Dashboard:   http://localhost:5173
echo ====================================================================
pause

