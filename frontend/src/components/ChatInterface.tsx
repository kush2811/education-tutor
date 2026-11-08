import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Mic, Paperclip, Bot, User } from 'lucide-react';
import { StudySession } from '../types';
import { MathRenderer } from './MathRenderer';

interface ChatInterfaceProps {
  session: StudySession | null;
  onSendMessage: (content: string, contentType?: string) => Promise<void>;
  onOpenUpload: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  session,
  onSendMessage,
  onOpenUpload,
}) => {
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || sending || !session) return;

    const text = inputText;
    setInputText('');
    setSending(true);
    try {
      await onSendMessage(text);
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSending(false);
    }
  };

  /**
   * Helper to parse markdown math delimiters like $$ ... $$ or $ ... $
   */
  const renderMessageContent = (content: string) => {
    // If the message contains LaTeX math delimiters
    const parts = content.split(/(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)/g);

    return parts.map((part, index) => {
      if (part.startsWith('$$') && part.endsWith('$$')) {
        const math = part.slice(2, -2).trim();
        return <MathRenderer key={index} math={math} block={true} />;
      } else if (part.startsWith('$') && part.endsWith('$')) {
        const math = part.slice(1, -1).trim();
        return <MathRenderer key={index} math={math} block={false} />;
      }
      return <span key={index}>{part}</span>;
    });
  };

  if (!session) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-50">
        <div className="w-16 h-16 rounded-2xl bg-sky-100 text-sky-600 flex items-center justify-center mb-4 shadow-sm">
          <Sparkles className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">No Session Selected</h3>
        <p className="text-sm text-slate-500 max-w-sm mt-1">
          Select an existing session from the sidebar or click "New" to start learning with your AI multimodal tutor.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Session Title Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
        <div>
          <span className="text-[11px] font-semibold text-sky-600 uppercase tracking-wider">
            {session.subject}
          </span>
          <h2 className="text-base font-bold text-slate-800">{session.title}</h2>
        </div>
        <div className="text-xs text-slate-400">
          Socratic Mode: <span className="font-semibold text-emerald-600">Active</span>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {session.messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center mx-auto mb-3">
              <Bot className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-slate-700 text-sm">Welcome to your tutoring session!</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
              Ask any question, type a math formula like $f(x) = x^2 + 2x + 1$, or describe a problem you'd like to work through step by step.
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
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white ${
                    isUser ? 'bg-sky-600' : 'bg-slate-800'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-sky-600 text-white rounded-tr-none shadow-sm'
                      : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none shadow-sm'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{renderMessageContent(msg.content)}</div>
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
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="bg-white border-t border-slate-200 p-4">
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
              placeholder="Ask a question or formulate a problem... (Press Enter to send, Shift+Enter for newline)"
              className="flex-1 text-sm bg-transparent border-none outline-none resize-none max-h-32 min-h-[44px] py-1 text-slate-800 placeholder-slate-400"
              rows={1}
            />

            <div className="flex items-center gap-1.5 shrink-0">
              <button
                type="button"
                onClick={onOpenUpload}
                className="p-2 text-slate-400 hover:text-sky-600 hover:bg-slate-50 rounded-xl transition-colors"
                title="Attach problem screenshot or diagram"
              >
                <Paperclip className="w-4 h-4" />
              </button>

              <button
                type="button"
                className="p-2 text-slate-400 hover:text-sky-600 hover:bg-slate-50 rounded-xl transition-colors"
                title="Voice input (speech-to-text)"
              >
                <Mic className="w-4 h-4" />
              </button>

              <button
                type="submit"
                disabled={!inputText.trim() || sending}
                className="p-2 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-200 text-white rounded-xl transition-all shadow-sm shadow-sky-200 disabled:shadow-none"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between px-2 text-[11px] text-slate-400">
            <span>Tip: Enclose formulas in <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-600">$...$</code> for LaTeX math rendering</span>
            <span>Multimodal Pipeline Ready</span>
          </div>
        </form>
      </div>
    </div>
  );
};
