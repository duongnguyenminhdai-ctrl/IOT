import React, { useState } from 'react';
import { History, Image as ImageIcon, Trash2, X, AlertOctagon, UserX, AlertCircle } from 'lucide-react';

export default function IncidentLogs({ incidents, onClearLogs }) {
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);

  const getEventBadge = (type) => {
    switch (type) {
      case 'LOITERING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <UserX className="w-3.5 h-3.5" />
            Lảng Vảng ({type})
          </span>
        );
      case 'DOOR_BREACH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertOctagon className="w-3.5 h-3.5" />
            Cạy/Mở Cửa ({type})
          </span>
        );
      case 'MANUAL_ALARM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <AlertCircle className="w-3.5 h-3.5" />
            Báo Động Khẩn
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-700 text-slate-300">
            {type}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-slate-200">Nhật Ký Sự Cố & Cảnh Báo (Incident Logs)</h3>
          <span className="bg-slate-800 text-slate-300 text-xs px-2 py-0.5 rounded-full font-mono">
            {incidents?.length || 0}
          </span>
        </div>
        {incidents && incidents.length > 0 && (
          <button
            onClick={onClearLogs}
            className="flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 transition px-2 py-1 rounded hover:bg-slate-800"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Xóa lịch sử
          </button>
        )}
      </div>

      <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/70 text-xs uppercase text-slate-400 sticky top-0">
            <tr>
              <th className="px-4 py-3">Thời gian</th>
              <th className="px-4 py-3">Sự kiện</th>
              <th className="px-4 py-3">Nội dung chi tiết</th>
              <th className="px-4 py-3">Thời gian ở lại</th>
              <th className="px-4 py-3 text-right">Ảnh bằng chứng</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {(!incidents || incidents.length === 0) ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-slate-500">
                  Chưa ghi nhận sự cố an ninh nào.
                </td>
              </tr>
            ) : (
              incidents.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-slate-400 whitespace-nowrap">
                    {log.timestamp}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {getEventBadge(log.event_type)}
                  </td>
                  <td className="px-4 py-3 text-slate-200 max-w-xs truncate">
                    {log.description}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {log.dwell_time ? `${log.dwell_time.toFixed(1)}s` : '-'}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {log.snapshot_url ? (
                      <button
                        onClick={() => setSelectedSnapshot(log.snapshot_url)}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 rounded text-xs hover:bg-indigo-600 hover:text-white transition"
                      >
                        <ImageIcon className="w-3.5 h-3.5" />
                        Xem ảnh
                      </button>
                    ) : (
                      <span className="text-xs text-slate-600">Không có</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Snapshot Preview Modal */}
      {selectedSnapshot && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-3xl w-full overflow-hidden shadow-2xl">
            <div className="flex justify-between items-center px-4 py-3 border-b border-slate-800">
              <h4 className="font-semibold text-slate-200 text-sm">Ảnh Chụp Bằng Chứng Sự Cố (Edge Snapshot)</h4>
              <button
                onClick={() => setSelectedSnapshot(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-3 bg-black flex justify-center">
              <img
                src={selectedSnapshot}
                alt="Security Evidence Snapshot"
                className="max-h-[75vh] w-auto object-contain rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

