import React, { useState, useEffect } from 'react';
import { Shield, Radio, BellRing } from 'lucide-react';
import LiveFeed from './components/LiveFeed';
import DeviceStatus from './components/DeviceStatus';
import QuickActions from './components/QuickActions';
import IncidentLogs from './components/IncidentLogs';

export default function App() {
  const [status, setStatus] = useState(null);
  const [incidents, setIncidents] = useState([]);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/system/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Error fetching system status:', err);
    }
  };

  const fetchIncidents = async () => {
    try {
      const res = await fetch('/api/incidents/');
      if (res.ok) {
        const data = await res.json();
        setIncidents(data.incidents || []);
      }
    } catch (err) {
      console.error('Error fetching incidents:', err);
    }
  };

  const handleClearLogs = async () => {
    try {
      await fetch('/api/incidents/clear', { method: 'DELETE' });
      setIncidents([]);
    } catch (err) {
      console.error('Error clearing incidents:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchIncidents();

    // 1-second interval polling for real-time status
    const statusInterval = setInterval(fetchStatus, 1000);
    // 3-second interval polling for incidents list
    const incidentsInterval = setInterval(fetchIncidents, 3000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(incidentsInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-40 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600 rounded-lg text-white shadow-md shadow-indigo-600/30">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Hệ Thống IoT Giám Sát Cửa & Hành Vi Bất Thường
              <span className="text-xs font-mono font-medium bg-indigo-950 border border-indigo-700 text-indigo-300 px-2 py-0.5 rounded">
                Edge AI + ESP32
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Kiến trúc Hybrid Edge AI (FastAPI + YOLOv8n + Mosquitto + React 18)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {status?.alarm_active && (
            <div className="flex items-center gap-2 px-3 py-1 bg-rose-600/20 border border-rose-500 rounded-full text-rose-400 text-xs font-bold animate-pulse">
              <BellRing className="w-4 h-4" />
              CẢNH BÁO BÁO ĐỘNG ĐANG KÍCH HOẠT!
            </div>
          )}
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span>Mosquitto Broker: {status?.mqtt_connected ? 'Kết nối' : 'Ngắt kết nối'}</span>
          </div>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Device Status Bar */}
        <DeviceStatus status={status} />

        {/* Central Content Area: Video Live Feed & Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <LiveFeed />
          </div>
          <div className="flex flex-col gap-6">
            <QuickActions status={status} onRefresh={fetchStatus} />
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex-1 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                  Thông Tin Ranh Giới Bảo Mật
                </h3>
                <ul className="text-xs text-slate-400 space-y-2">
                  <li className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span>Cảm biến cửa từ:</span>
                    <span className="font-mono text-slate-200">MC-38 (GPIO 14 - Interrupt)</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span>Cảm biến chuyển động:</span>
                    <span className="font-mono text-slate-200">PIR HC-SR501 (GPIO 13)</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span>Thiết bị phát âm báo:</span>
                    <span className="font-mono text-slate-200">Active Buzzer 5V (GPIO 27)</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span>Thiết bị đóng cắt:</span>
                    <span className="font-mono text-slate-200">Relay 5V 1-CH (GPIO 26)</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span>Màn hình hiển thị:</span>
                    <span className="font-mono text-slate-200">OLED SSD1306 (I2C 21/22)</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>Nút nhấn khẩn cấp:</span>
                    <span className="font-mono text-slate-200">GPIO 15 (Pull-up)</span>
                  </li>
                </ul>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500">
                Khi hệ thống ở chế độ <b>ARMED</b>, bất kỳ hành vi lảng vảng trước ROI &gt; 20s hoặc cạy mở cửa MC-38 sẽ lập tức kích hoạt còi, chụp ảnh lưu DB và gửi tin nhắn cảnh báo Telegram.
              </div>
            </div>
          </div>
        </div>

        {/* Incident Logs Table */}
        <IncidentLogs incidents={incidents} onClearLogs={handleClearLogs} />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        Course Project: Hệ thống IoT giám sát và phát hiện xâm nhập trước cửa nhà dựa trên phân tích hành vi bất thường &copy; 2026
      </footer>
    </div>
  );
}

