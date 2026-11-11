import React, { useState, useRef } from 'react';
import { Camera, RefreshCw, Crosshair, Check, Undo2, AlertCircle } from 'lucide-react';

export default function LiveFeed() {
  const [streamKey, setStreamKey] = useState(Date.now());
  const [hasError, setHasError] = useState(false);
  
  // Interactive ROI Calibration states
  const [isCalibratingROI, setIsCalibratingROI] = useState(false);
  const [roiPoints, setRoiPoints] = useState([]); // List of [xPct, yPct]
  const [savingROI, setSavingROI] = useState(false);
  const [roiMessage, setRoiMessage] = useState(null);
  const videoContainerRef = useRef(null);

  const handleRefresh = () => {
    setHasError(false);
    setStreamKey(Date.now());
  };

  const handleContainerClick = (e) => {
    if (!isCalibratingROI) return;
    if (roiPoints.length >= 8) return; // Max 8 points for polygon

    const rect = videoContainerRef.current.getBoundingClientRect();
    const xPct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const yPct = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));

    setRoiPoints([...roiPoints, [parseFloat(xPct.toFixed(3)), parseFloat(yPct.toFixed(3))]]);
  };

  const handleSaveROI = async () => {
    if (roiPoints.length < 3) {
      setRoiMessage("Cần chọn ít nhất 3 điểm để tạo thành đa giác ROI.");
      return;
    }

    try {
      setSavingROI(true);
      const res = await fetch('/api/stream/roi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points: roiPoints })
      });
      if (res.ok) {
        setRoiMessage("Cập nhật vùng ROI thành công!");
        setTimeout(() => {
          setIsCalibratingROI(false);
          setRoiPoints([]);
          setRoiMessage(null);
          handleRefresh();
        }, 1200);
      } else {
        setRoiMessage("Lỗi máy chủ khi cập nhật ROI.");
      }
    } catch (err) {
      console.error(err);
      setRoiMessage("Lỗi kết nối tới Backend.");
    } finally {
      setSavingROI(false);
    }
  };

  const handleCancelROI = () => {
    setIsCalibratingROI(false);
    setRoiPoints([]);
    setRoiMessage(null);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col">
      {/* Header */}
      <div className="bg-slate-800/80 px-4 py-3 border-b border-slate-700/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Camera className="w-5 h-5 text-indigo-400" />
          <h2 className="font-semibold text-slate-200">Camera Cửa Chính (YOLOv8 Edge AI)</h2>
          <span className="flex h-2 w-2 relative ml-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs text-emerald-400 uppercase font-mono tracking-wider ml-1">LIVE</span>
        </div>
        
        <div className="flex items-center gap-2">
          {!isCalibratingROI ? (
            <button
              onClick={() => { setIsCalibratingROI(true); setRoiPoints([]); }}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition"
              title="Vẽ lại vùng ranh giới ROI cửa"
            >
              <Crosshair className="w-3.5 h-3.5 text-indigo-400" />
              Cân chỉnh ROI
            </button>
          ) : (
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleSaveROI}
                disabled={savingROI || roiPoints.length < 3}
                className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                Lưu ({roiPoints.length})
              </button>
              <button
                onClick={handleCancelROI}
                className="flex items-center gap-1 px-2 py-1 text-xs font-medium bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition"
              >
                <Undo2 className="w-3.5 h-3.5" />
                Hủy
              </button>
            </div>
          )}

          <button
            onClick={handleRefresh}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            title="Làm mới luồng video"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Video Stream + Interactive Calibration Overlay */}
      <div 
        ref={videoContainerRef}
        onClick={handleContainerClick}
        className={`relative bg-black flex-1 min-h-[420px] flex items-center justify-center select-none overflow-hidden ${
          isCalibratingROI ? 'cursor-crosshair' : ''
        }`}
      >
        {hasError ? (
          <div className="text-center p-6">
            <p className="text-rose-400 font-medium mb-2">Không thể tải luồng video từ Edge AI Server</p>
            <p className="text-xs text-slate-400 mb-4">Vui lòng kiểm tra lại webcam USB và FastAPI Backend</p>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition"
            >
              Thử lại
            </button>
          </div>
        ) : (
          <>
            <img
              key={streamKey}
              src={`/api/stream/video_feed?t=${streamKey}`}
              alt="AI Security Stream"
              className="w-full h-full object-contain max-h-[600px] pointer-events-none"
              onError={() => setHasError(true)}
            />

            {/* Visual preview points when user clicks to calibrate ROI */}
            {isCalibratingROI && (
              <div className="absolute inset-0 pointer-events-none">
                {/* SVG Polygon Preview */}
                {roiPoints.length >= 2 && (
                  <svg className="w-full h-full absolute inset-0">
                    <polygon
                      points={roiPoints.map(p => `${p[0] * 100}%,${p[1] * 100}%`).join(' ')}
                      fill="rgba(99, 102, 241, 0.25)"
                      stroke="#818cf8"
                      strokeWidth="2"
                      strokeDasharray="4"
                    />
                  </svg>
                )}
                {/* Markers */}
                {roiPoints.map((pt, idx) => (
                  <div
                    key={idx}
                    className="absolute w-4 h-4 -ml-2 -mt-2 bg-indigo-500 border-2 border-white rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow"
                    style={{ left: `${pt[0] * 100}%`, top: `${pt[1] * 100}%` }}
                  >
                    {idx + 1}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Guidance Overlay during Calibration */}
        {isCalibratingROI && (
          <div className="absolute top-3 left-3 bg-indigo-950/90 border border-indigo-700/80 px-3 py-1.5 rounded-lg text-xs text-indigo-200 backdrop-blur-sm pointer-events-none shadow-lg">
            Nhấp chuột các góc trên màn hình để đặt vùng ranh giới trước cửa ({roiPoints.length} điểm đã chọn)
          </div>
        )}

        {/* Notification Toast */}
        {roiMessage && (
          <div className="absolute bottom-4 bg-slate-900 border border-slate-700 text-white text-xs px-4 py-2 rounded-lg shadow-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            {roiMessage}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="px-4 py-2 bg-slate-950 text-xs text-slate-400 border-t border-slate-800/80 flex justify-between items-center">
        <span>Vùng giám sát ROI: <b>Đa giác bảo vệ cửa</b> | Mô hình: <b>YOLOv8n + ByteTrack</b></span>
        <span>Ngưỡng lảng vảng: <b>20s</b></span>
      </div>
    </div>
  );
}
