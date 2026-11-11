import React, { useState } from 'react';
import { Shield, ShieldOff, VolumeX, AlertTriangle, Loader2 } from 'lucide-react';

export default function QuickActions({ status, onRefresh }) {
  const [loadingAction, setLoadingAction] = useState(null);

  const isArmed = status?.is_armed ?? false;
  const isAlarm = status?.alarm_active ?? false;

  const handleAction = async (endpoint, actionName) => {
    try {
      setLoadingAction(actionName);
      await fetch(`/api/system/${endpoint}`, { method: 'POST' });
      if (onRefresh) await onRefresh();
    } catch (err) {
      console.error(`Action ${actionName} failed:`, err);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <h3 className="text-base font-semibold text-slate-200 mb-4 flex items-center gap-2">
        <Shield className="w-5 h-5 text-indigo-400" />
        Bảng Điều Khiển Nhanh (Quick Actions)
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Arm / Disarm Toggle */}
        <button
          onClick={() => handleAction(isArmed ? 'disarm' : 'arm', 'arm_toggle')}
          disabled={loadingAction !== null}
          className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition shadow-md ${
            isArmed
              ? 'bg-amber-600 hover:bg-amber-700 text-white'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
          }`}
        >
          {loadingAction === 'arm_toggle' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : isArmed ? (
            <>
              <ShieldOff className="w-5 h-5" />
              Tắt Bảo Vệ (Disarm)
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              Kích Hoạt Bảo Vệ (Arm)
            </>
          )}
        </button>

        {/* Mute Alarm */}
        <button
          onClick={() => handleAction('mute-alarm', 'mute')}
          disabled={loadingAction !== null || !isAlarm}
          className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition shadow-md ${
            isAlarm
              ? 'bg-slate-700 hover:bg-slate-600 text-white animate-pulse'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          {loadingAction === 'mute' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <VolumeX className="w-5 h-5" />
              Tắt Còi / Reset Báo Động
            </>
          )}
        </button>

        {/* Manual Trigger Emergency */}
        <button
          onClick={() => handleAction('trigger-alarm', 'panic')}
          disabled={loadingAction !== null}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium bg-rose-600 hover:bg-rose-700 text-white transition shadow-md"
        >
          {loadingAction === 'panic' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <AlertTriangle className="w-5 h-5" />
              Báo Động Khẩn Cấp (Panic)
            </>
          )}
        </button>
      </div>
    </div>
  );
}

