import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle, X } from 'lucide-react';
import { api } from '../services/api';
import { UploadedFileResponse } from '../types';

interface FileUploadModalProps {
  isOpen: boolean;
  sessionId?: string;
  onClose: () => void;
  onUploadSuccess: (response: UploadedFileResponse) => void;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  sessionId,
  onClose,
  onUploadSuccess,
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const handleFileSelect = (file: File) => {
    setError(null);
    setSelectedFile(file);
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadFile(selectedFile, sessionId);
      onUploadSuccess(res);
      onClose();
    } catch (err: any) {
      setError(err.message || 'File upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-6 w-full max-w-lg shadow-2xl border border-slate-100 relative animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-lg font-bold text-slate-900 mb-1">Upload Problem or Worksheet</h3>
        <p className="text-xs text-slate-500 mb-4">
          Upload a photo of handwritten equations, a textbook diagram, or a PDF problem set.
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center ${
            dragOver ? 'border-sky-500 bg-sky-50' : 'border-slate-200 hover:border-slate-300 bg-slate-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.pdf,.docx"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelect(e.target.files[0]);
              }
            }}
          />

          {previewUrl ? (
            <div className="flex flex-col items-center">
              <img src={previewUrl} alt="Preview" className="max-h-48 rounded-xl object-contain shadow-sm mb-3" />
              <span className="text-xs font-semibold text-slate-700">{selectedFile?.name}</span>
              <span className="text-[11px] text-slate-400">Click or drag another file to replace</span>
            </div>
          ) : selectedFile ? (
            <div className="flex flex-col items-center">
              <FileText className="w-12 h-12 text-sky-600 mb-2" />
              <span className="text-xs font-semibold text-slate-700">{selectedFile.name}</span>
              <span className="text-[11px] text-slate-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
            </div>
          ) : (
            <>
              <div className="w-12 h-12 rounded-2xl bg-sky-100 text-sky-600 flex items-center justify-center mb-3">
                <UploadCloud className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-slate-700">Drag & drop your file here, or browse</p>
              <p className="text-xs text-slate-400 mt-1">Supports PNG, JPG, WEBP, PDF, DOCX (up to 50MB)</p>
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="px-5 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-700 disabled:bg-slate-200 text-white rounded-xl shadow-sm transition-colors flex items-center gap-1.5"
          >
            {uploading ? 'Uploading...' : 'Upload & Attach'}
          </button>
        </div>
      </div>
    </div>
  );
};
