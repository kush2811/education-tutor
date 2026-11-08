import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Mic,
  MicOff,
  Paperclip,
  Bot,
  User as UserIcon,
  X,
  FileText,
  Image as ImageIcon,
  Video as VideoIcon,
  Music,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { StudySession, MessageCitation } from '../types';
import { TutorResponse } from './TutorResponse';

interface ChatInterfaceProps {
  session: StudySession | null;
  onSendMessage: (content: string, contentType?: string, citations?: MessageCitation[]) => Promise<void>;
  onOpenUpload: () => void;
  onPlayVoice: (text: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  session,
  onSendMessage,
  onOpenUpload,
  onPlayVoice,
}) => {
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachedPreviewUrl, setAttachedPreviewUrl] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const hiddenFileInputRef = useRef<HTMLInputElement | null>(null);
  const recordingTimerRef = useRef<number | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.messages, sending]);

  // Handle Voice Recording Simulation (functional timer + mock audio capture)
  const handleToggleRecord = () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
      // Append audio inquiry prompt
      setInputText((prev) => (prev ? `${prev} [Voice Question: ~${recordingSeconds}s]` : `[Voice Question: ~${recordingSeconds}s]`));
      setRecordingSeconds(0);
    } else {
      // Start recording
      setIsRecording(true);
      setRecordingSeconds(0);
      recordingTimerRef.current = window.setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    }
  };

  const handleFileAttach = (file: File) => {
    setAttachedFile(file);
    setErrorMessage(null);
    if (file.type.startsWith('image/')) {
      setAttachedPreviewUrl(URL.createObjectURL(file));
    } else {
      setAttachedPreviewUrl(null);
    }
  };

  const handleRemoveAttachment = () => {
    setAttachedFile(null);
    setAttachedPreviewUrl(null);
    setUploadProgress(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!inputText.trim() && !attachedFile) || sending || !session) return;

    setSending(true);
    setErrorMessage(null);

    try {
      let finalContent = inputText.trim();
      let contentType = 'text';

      // If there is an attached file, simulate/perform upload progress
      if (attachedFile) {
        setUploadProgress(20);
        await new Promise((r) => setTimeout(r, 200));
        setUploadProgress(65);
        await new Promise((r) => setTimeout(r, 200));
        setUploadProgress(100);

        contentType = attachedFile.type.startsWith('image/')
          ? 'image'
          : attachedFile.type.includes('pdf')
          ? 'document'
          : attachedFile.type.startsWith('video/')
          ? 'video'
          : attachedFile.type.startsWith('audio/')
          ? 'audio'
          : 'multimodal';

        const fileNote = `[Attached ${contentType.toUpperCase()}: ${attachedFile.name} (${(attachedFile.size / 1024).toFixed(1)} KB)]`;
        finalContent = finalContent ? `${fileNote}\n${finalContent}` : fileNote;
      }

      setInputText('');
      handleRemoveAttachment();
      await onSendMessage(finalContent, contentType);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to send message. Please try again.');
    } finally {
      setSending(false);
      setUploadProgress(null);
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <ImageIcon className="w-4 h-4 text-sky-500" />;
    if (file.type.startsWith('video/')) return <VideoIcon className="w-4 h-4 text-purple-500" />;
    if (file.type.startsWith('audio/')) return <Music className="w-4 h-4 text-amber-500" />;
    return <FileText className="w-4 h-4 text-emerald-500" />;
  };

  if (!session) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-50">
        <div className="w-16 h-16 rounded-3xl bg-sky-100 text-sky-600 flex items-center justify-center mb-4 shadow-sm">
          <Sparkles className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">No Tutoring Session Active</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Select an existing session from the sidebar or click "New" to start guided problem solving.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Session Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-2xs">
        <div>
          <span className="text-[10px] font-bold text-sky-600 uppercase tracking-wider">
            {session.subject}
          </span>
          <h2 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            {session.title}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60">
            Socratic Mode Active
          </span>
        </div>
      </div>

      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 text-xs text-rose-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-500 hover:text-rose-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {session.messages.length === 0 ? (
          <div className="text-center py-12 max-w-md mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-sky-100 text-sky-600 flex items-center justify-center mx-auto mb-3 shadow-sm">
              <Bot className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-slate-800 text-sm">Welcome to your guided session!</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Ask any STEM question, attach a photo of your handwritten math problem, or upload a worksheet.
              Your tutor will guide you step by step.
            </p>
          </div>
        ) : (
          session.messages.map((msg) => {
            const isUser = msg.sender_role === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
              >
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white shadow-xs ${
                    isUser ? 'bg-sky-600' : 'bg-slate-800'
                  }`}
                >
                  {isUser ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div
                  className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'bg-sky-600 text-white rounded-tr-none shadow-md shadow-sky-600/10'
                      : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none shadow-sm'
                  }`}
                >
                  {isUser ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <TutorResponse
                      content={msg.content}
                      citations={msg.citations}
                      onPlayAudio={() => onPlayVoice(msg.content)}
                    />
                  )}

                  <div
                    className={`text-[10px] mt-2 font-medium ${
                      isUser ? 'text-sky-200 text-right' : 'text-slate-400'
                    }`}
                  >
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            );
          })
        )}

        {/* Sending / Thinking Indicator */}
        {sending && (
          <div className="flex gap-3 max-w-xl mr-auto animate-in fade-in duration-200">
            <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-white border border-slate-200/80 rounded-2xl rounded-tl-none p-4 shadow-sm flex items-center gap-3">
              <Loader2 className="w-4 h-4 text-sky-600 animate-spin" />
              <div className="text-xs text-slate-600 font-medium">
                AI Tutor is analyzing your problem and preparing Socratic guidance...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Dock & Attachments */}
      <div className="bg-white border-t border-slate-200 p-4">
        {/* File Preview Attachment Pill */}
        {attachedFile && (
          <div className="mb-2 max-w-md bg-slate-100 rounded-xl p-2.5 flex items-center justify-between border border-slate-200 text-xs animate-in slide-in-from-bottom-1">
            <div className="flex items-center gap-2 truncate">
              {attachedPreviewUrl ? (
                <img src={attachedPreviewUrl} alt="Thumbnail" className="w-8 h-8 rounded-lg object-cover" />
              ) : (
                <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shrink-0">
                  {getFileIcon(attachedFile)}
                </div>
              )}
              <div className="truncate">
                <span className="font-semibold text-slate-800 truncate block">{attachedFile.name}</span>
                <span className="text-[10px] text-slate-400">{(attachedFile.size / 1024).toFixed(1)} KB</span>
              </div>
            </div>
            <button
              onClick={handleRemoveAttachment}
              className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Upload Progress Bar */}
        {uploadProgress !== null && (
          <div className="mb-2 w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-sky-600 h-1.5 transition-all duration-200"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        )}

        {/* Hidden File Input */}
        <input
          ref={hiddenFileInputRef}
          type="file"
          accept="image/*,.pdf,.docx,audio/*,video/*"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileAttach(e.target.files[0]);
            }
          }}
        />

        {/* Active Recording Pill */}
        {isRecording && (
          <div className="mb-2 bg-rose-50 border border-rose-200 rounded-xl px-3 py-1.5 flex items-center justify-between text-xs text-rose-700 animate-pulse">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-ping" />
              <span className="font-semibold">Recording speech: {recordingSeconds}s</span>
            </div>
            <button
              onClick={handleToggleRecord}
              className="text-[11px] font-bold text-rose-800 underline hover:text-rose-900"
            >
              Finish & Attach
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <div className="flex items-center gap-2 border border-slate-300 rounded-2xl px-4 py-2 bg-white focus-within:border-sky-500 focus-within:ring-2 focus-within:ring-sky-100 transition-all">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask a question or describe a problem... (Press Enter to send, Shift+Enter for newline)"
              className="flex-1 text-xs sm:text-sm bg-transparent border-none outline-none resize-none max-h-32 min-h-[44px] py-1 text-slate-800 placeholder-slate-400"
              rows={1}
            />

            <div className="flex items-center gap-1.5 shrink-0">
              {/* Quick file attach */}
              <button
                type="button"
                onClick={() => hiddenFileInputRef.current?.click()}
                className="p-2 text-slate-400 hover:text-sky-600 hover:bg-slate-50 rounded-xl transition-colors"
                title="Attach image, PDF, DOCX, audio or video"
              >
                <Paperclip className="w-4 h-4" />
              </button>

              {/* Advanced modal upload */}
              <button
                type="button"
                onClick={onOpenUpload}
                className="p-2 text-slate-400 hover:text-sky-600 hover:bg-slate-50 rounded-xl transition-colors"
                title="Open upload modal with preview"
              >
                <ImageIcon className="w-4 h-4" />
              </button>

              {/* Microphone toggle */}
              <button
                type="button"
                onClick={handleToggleRecord}
                className={`p-2 rounded-xl transition-colors ${
                  isRecording ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-sky-600 hover:bg-slate-50'
                }`}
                title={isRecording ? 'Stop recording' : 'Speak your question (STT)'}
              >
                {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              {/* Submit send */}
              <button
                type="submit"
                disabled={(!inputText.trim() && !attachedFile) || sending}
                className="p-2.5 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-200 text-white rounded-xl transition-all shadow-sm shadow-sky-200 disabled:shadow-none"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between px-2 text-[11px] text-slate-400">
            <span>
              Tip: Use <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-600">$formula$</code> for KaTeX math rendering
            </span>
            <span className="hidden sm:inline">Images • PDFs • DOCX • Audio • Video Ready</span>
          </div>
        </form>
      </div>
    </div>
  );
};
