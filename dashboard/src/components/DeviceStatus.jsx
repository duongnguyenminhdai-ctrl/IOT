import React from 'react';
import { DoorOpen, DoorClosed, Activity, ShieldCheck, ShieldAlert, BellRing, BellOff, Wifi, WifiOff } from 'lucide-react';

export default function DeviceStatus({ status }) {
  const isArmed = status?.is_armed ?? false;
  const isAlarm = status?.alarm_active ?? false;
  const doorOpen = status?.door_state === 'OPEN';
  const pirMotion = status?.pir_state === 'MOTION';
  const mqttOnline = status?.mqtt_connected ?? false;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {/* System Arm Status */}
      <div className={`p-4 rounded-xl border transition-all ${
        isArmed 
          ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-400' 
          : 'bg-slate-900 border-slate-800 text-slate-400'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Trạng thái bảo vệ</span>
          {isArmed ? <ShieldCheck className="w-5 h-5 text-emerald-400" /> : <ShieldAlert className="w-5 h-5 text-slate-400" />}
        </div>
        <div className="text-xl font-bold">
          {isArmed ? 'ĐÃ KÍCH HOẠT (ARMED)' : 'TẮT BẢO VỆ (DISARMED)'}
        </div>
        <p className="text-xs text-slate-500 mt-1">
          {isArmed ? 'Tự động kích hoạt còi khi mở cửa' : 'Chế độ an toàn đang tắt'}
        </p>
      </div>

      {/* Door Status */}
      <div className={`p-4 rounded-xl border transition-all ${
        doorOpen 
          ? 'bg-rose-950/40 border-rose-500/60 text-rose-400 shadow-rose-900/20 shadow-lg' 
          : 'bg-slate-900 border-slate-800 text-slate-300'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Cửa chính (MC-38)</span>
          {doorOpen ? <DoorOpen className="w-5 h-5 text-rose-400 animate-bounce" /> : <DoorClosed className="w-5 h-5 text-emerald-400" />}
        </div>
        <div className="text-xl font-bold">
          {doorOpen ? 'ĐANG MỞ' : 'ĐÃ ĐÓNG'}
        </div>
        <p className="text-xs text-slate-500 mt-1">
          GPIO 14 (Hardware Interrupt)
        </p>
      </div>

      {/* PIR Motion */}
      <div className={`p-4 rounded-xl border transition-all ${
        pirMotion 
          ? 'bg-amber-950/40 border-amber-500/60 text-amber-400' 
          : 'bg-slate-900 border-slate-800 text-slate-300'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Chuyển động (PIR HC-SR501)</span>
          <Activity className={`w-5 h-5 ${pirMotion ? 'text-amber-400 animate-pulse' : 'text-slate-500'}`} />
        </div>
        <div className="text-xl font-bold">
          {pirMotion ? 'CÓ CHUYỂN ĐỘNG' : 'YÊN TĨNH'}
        </div>
        <p className="text-xs text-slate-500 mt-1">
          GPIO 13
        </p>
      </div>

      {/* Alarm & Buzzer */}
      <div className={`p-4 rounded-xl border transition-all ${
        isAlarm 
          ? 'bg-rose-950/50 border-rose-500 text-rose-400 animate-pulse shadow-lg shadow-rose-950' 
          : 'bg-slate-900 border-slate-800 text-slate-300'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Còi & Rơ-le (Buzzer/Relay)</span>
          {isAlarm ? <BellRing className="w-5 h-5 text-rose-400" /> : <BellOff className="w-5 h-5 text-slate-500" />}
        </div>
        <div className="text-xl font-bold">
          {isAlarm ? 'ĐANG BÁO ĐỘNG!' : 'BÌNH THƯỜNG'}
        </div>
        <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
          MQTT: {mqttOnline ? <span className="text-emerald-400 font-medium">Đã kết nối</span> : <span className="text-rose-400 font-medium">Mất kết nối</span>}
        </p>
      </div>
    </div>
  );
}

