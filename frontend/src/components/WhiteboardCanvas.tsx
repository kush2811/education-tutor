import React, { useRef, useState, useEffect } from 'react';
import { Eraser, Pen, Trash2, Download } from 'lucide-react';

interface WhiteboardCanvasProps {
  onExportImage?: (dataUrl: string) => void;
}

export const WhiteboardCanvas: React.FC<WhiteboardCanvasProps> = ({ onExportImage }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [strokeColor, setStrokeColor] = useState('#0f172a');
  const [strokeWidth, setStrokeWidth] = useState(3);
  const [mode, setMode] = useState<'pen' | 'eraser'>('pen');

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Fill white background on init
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }, []);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = mode === 'eraser' ? '#ffffff' : strokeColor;
    ctx.lineWidth = mode === 'eraser' ? strokeWidth * 5 : strokeWidth;
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    if (onExportImage && canvasRef.current) {
      onExportImage(canvasRef.current.toDataURL('image/png'));
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  };

  const downloadCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `whiteboard-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Canvas Toolbar */}
      <div className="px-4 py-2 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode('pen')}
            className={`p-2 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
              mode === 'pen' ? 'bg-sky-600 text-white' : 'hover:bg-slate-200 text-slate-700'
            }`}
            title="Pen"
          >
            <Pen className="w-3.5 h-3.5" />
            Pen
          </button>
          <button
            onClick={() => setMode('eraser')}
            className={`p-2 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
              mode === 'eraser' ? 'bg-sky-600 text-white' : 'hover:bg-slate-200 text-slate-700'
            }`}
            title="Eraser"
          >
            <Eraser className="w-3.5 h-3.5" />
            Eraser
          </button>

          {mode === 'pen' && (
            <>
              <div className="flex items-center gap-1.5 ml-2 border-l border-slate-200 pl-2">
                {[2, 4, 6].map((w) => (
                  <button
                    key={w}
                    onClick={() => setStrokeWidth(w)}
                    className={`px-2 py-0.5 text-[10px] font-bold rounded border ${
                      strokeWidth === w ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200'
                    }`}
                  >
                    {w}px
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1.5 ml-2 border-l border-slate-200 pl-2">
                {['#0f172a', '#2563eb', '#dc2626', '#16a34a'].map((c) => (
                  <button
                    key={c}
                    onClick={() => setStrokeColor(c)}
                    className={`w-5 h-5 rounded-full border-2 transition-transform ${
                      strokeColor === c ? 'border-sky-500 scale-110' : 'border-transparent'
                    }`}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={clearCanvas}
            className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors text-xs flex items-center gap-1"
            title="Clear board"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={downloadCanvas}
            className="p-1.5 text-slate-500 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition-colors text-xs flex items-center gap-1"
            title="Export drawing"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 bg-white relative flex items-center justify-center p-2">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          className="w-full h-full border border-dashed border-slate-200 rounded-xl cursor-crosshair bg-white"
        />
      </div>
    </div>
  );
};
