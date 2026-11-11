import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
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
  GraduationCap,
} from 'lucide-react';
import { StudySession } from '../types';
import { TutorResponse } from './TutorResponse';

interface ChatInterfaceProps {
  session: StudySession | null;
  onSendMessage: (content: string, contentType?: string, attachedFile?: File) => Promise<void>;
  onPlayVoice: (text: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  session,
  onSendMessage,
  onPlayVoice,
}) => {
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [pendingUserText, setPendingUserText] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachedPreviewUrl, setAttachedPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const latestMessageRef = useRef<HTMLDivElement | null>(null);
  const prevMsgCountRef = useRef<number>(0);
  const prevSessionIdRef = useRef<string | null>(null);
  const hiddenFileInputRef = useRef<HTMLInputElement | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const currentMsgs = session?.messages || [];
    const currentId = session?.id || null;
    const isNewSession = currentId !== prevSessionIdRef.current;
    const msgAdded = currentMsgs.length > prevMsgCountRef.current;

    prevSessionIdRef.current = currentId;
    prevMsgCountRef.current = currentMsgs.length;

    if (pendingUserText || sending) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
      return;
    }

    if ((msgAdded || isNewSession) && latestMessageRef.current) {
      // Position the start of the latest AI response near the top of the scroll area so tall answers are never cut off
      const lastMsg = currentMsgs[currentMsgs.length - 1];
      if (lastMsg?.sender_role === 'assistant') {
        const targetTop = Math.max(0, latestMessageRef.current.offsetTop - 20);
        container.scrollTo({ top: targetTop, behavior: isNewSession ? 'auto' : 'smooth' });
        return;
      }
    }

    container.scrollTo({ top: container.scrollHeight, behavior: isNewSession ? 'auto' : 'smooth' });
  }, [session?.id, session?.messages?.length, sending, pendingUserText]);

  const handleToggleRecord = () => {
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorMessage('Voice dictation is not supported in this browser. You can attach an audio file or type directly.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          setInputText((prev) => (prev ? `${prev} ${transcript}` : transcript));
        }
      };

      recognition.onerror = (event: any) => {
        setErrorMessage(`Microphone error: ${event.error || 'Permission denied'}`);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      setErrorMessage(null);
      setIsRecording(true);
      recognition.start();
    } catch (err: any) {
      setErrorMessage(err?.message || 'Could not start voice recording.');
      setIsRecording(false);
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
    if (hiddenFileInputRef.current) {
      hiddenFileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!inputText.trim() && !attachedFile) || sending) return;

    const currentFile = attachedFile;
    let finalContent = inputText.trim();
    let contentType = 'text';

    if (currentFile) {
      contentType = currentFile.type.startsWith('image/')
        ? 'image'
        : currentFile.type.includes('pdf')
        ? 'pdf'
        : currentFile.type.startsWith('video/')
        ? 'video'
        : currentFile.type.startsWith('audio/')
        ? 'audio'
        : 'docx';

      const fileNote = `[Attached ${contentType.toUpperCase()}: ${currentFile.name}]`;
      finalContent = finalContent ? `${fileNote}\n${finalContent}` : fileNote;
    }

    setSending(true);
    setErrorMessage(null);
    setPendingUserText(finalContent);
    setInputText('');
    handleRemoveAttachment();

    try {
      await onSendMessage(finalContent, contentType, currentFile || undefined);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to send message. Please try again.');
    } finally {
      setPendingUserText(null);
      setSending(false);
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <ImageIcon className="w-4 h-4 text-sky-500" />;
    if (file.type.startsWith('video/')) return <VideoIcon className="w-4 h-4 text-purple-500" />;
    if (file.type.startsWith('audio/')) return <Music className="w-4 h-4 text-amber-500" />;
    return <FileText className="w-4 h-4 text-emerald-500" />;
  };

  const messages = session?.messages || [];
  const isEmptyChat = messages.length === 0 && !pendingUserText;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-white overflow-hidden">
      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="shrink-0 bg-rose-50 border-b border-rose-200 px-6 py-2.5 text-xs text-rose-700 flex items-center justify-between">
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

      {/* Main Message Stream */}
      <div ref={scrollContainerRef} className="flex-1 min-h-0 overflow-y-auto px-4 sm:px-6">
        {isEmptyChat ? (
          <div className="min-h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto py-8">
            <div className="w-12 h-12 rounded-2xl bg-sky-600 text-white flex items-center justify-center mb-4 shadow-sm">
              <GraduationCap className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-semibold text-slate-900 tracking-tight">
              What can I help you with today?
            </h2>
            <p className="text-sm text-slate-500 mt-2 max-w-md">
              Ask any question directly, or attach an image, PDF, Word document, audio, or video.
            </p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto py-5 space-y-5">
            {messages.map((msg, idx) => {
              const isUser = msg.sender_role === 'user';
              const isLatest = idx === messages.length - 1;
              return (
                <div
                  key={msg.id}
                  ref={isLatest ? latestMessageRef : null}
                  className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`rounded-2xl text-sm leading-relaxed ${
                      isUser
                        ? 'max-w-[80%] px-4 py-2.5 bg-slate-100 text-slate-900'
                        : 'flex-1 min-w-0 text-slate-800'
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
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-full bg-sky-600 text-white flex items-center justify-center shrink-0 mt-0.5">
                      <UserIcon className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {/* Optimistic Pending User Message */}
            {pendingUserText && (
              <div className="flex gap-3 justify-end">
                <div className="max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed bg-slate-100 text-slate-900">
                  <div className="whitespace-pre-wrap">{pendingUserText}</div>
                </div>
                <div className="w-8 h-8 rounded-full bg-sky-600 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <UserIcon className="w-4 h-4" />
                </div>
              </div>
            )}

            {/* Thinking Indicator */}
            {sending && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="flex items-center gap-2.5 py-2 text-sm text-slate-500">
                  <Loader2 className="w-4 h-4 text-sky-600 animate-spin" />
                  <span>Thinking...</span>
                </div>
              </div>
            )}

          </div>
        )}
      </div>

      {/* Centered Composer Input Bar */}
      <div className="shrink-0 bg-white border-t border-slate-100 px-4 pb-4 pt-3">
        <div className="max-w-3xl mx-auto">
          {/* Attached File Preview */}
          {attachedFile && (
            <div className="mb-2 max-w-md bg-slate-100 rounded-xl p-2 flex items-center justify-between border border-slate-200 text-xs">
              <div className="flex items-center gap-2 truncate">
                {attachedPreviewUrl ? (
                  <img src={attachedPreviewUrl} alt="Preview" className="w-8 h-8 rounded-lg object-cover" />
                ) : (
                  <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shrink-0">
                    {getFileIcon(attachedFile)}
                  </div>
                )}
                <div className="truncate">
                  <span className="font-medium text-slate-800 truncate block">{attachedFile.name}</span>
                  <span className="text-[10px] text-slate-500">{(attachedFile.size / 1024).toFixed(1)} KB</span>
                </div>
              </div>
              <button
                type="button"
                onClick={handleRemoveAttachment}
                className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

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

          <form onSubmit={handleSubmit}>
            <div className="flex items-end gap-2 border border-slate-300 rounded-2xl px-3 py-2 bg-slate-50/70 focus-within:bg-white focus-within:border-slate-400 focus-within:shadow-sm transition-all">
              <button
                type="button"
                onClick={() => hiddenFileInputRef.current?.click()}
                className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-200/60 rounded-xl transition-colors shrink-0"
                title="Attach file (Image, PDF, DOCX, Audio, Video)"
              >
                <Paperclip className="w-4 h-4" />
              </button>

              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Ask anything..."
                className="flex-1 text-sm bg-transparent border-none outline-none resize-none max-h-36 min-h-[36px] py-1.5 text-slate-900 placeholder-slate-400"
                rows={1}
              />

              <button
                type="button"
                onClick={handleToggleRecord}
                className={`p-2 rounded-xl transition-colors shrink-0 ${
                  isRecording
                    ? 'bg-rose-600 text-white animate-pulse'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
                title={isRecording ? 'Stop dictation' : 'Voice dictation'}
              >
                {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              <button
                type="submit"
                disabled={(!inputText.trim() && !attachedFile) || sending}
                className="p-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-xl transition-colors shrink-0"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>

          <div className="text-center text-[11px] text-slate-400 mt-1.5">
            Supports text, images, PDFs, DOCX, audio, and video. Press Enter to send.
          </div>
        </div>
      </div>
    </div>
  );
};
