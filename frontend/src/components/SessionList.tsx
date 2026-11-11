import React, { useState } from 'react';
import { SquarePen, MessageSquare, Trash2, Edit2, Check, X } from 'lucide-react';
import { StudySession } from '../types';

interface SessionListProps {
  sessions: StudySession[];
  activeSessionId: string | null;
  isOpen: boolean;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onRenameSession?: (id: string, newTitle: string) => void;
  onDeleteSession: (id: string) => void;
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  activeSessionId,
  isOpen,
  onSelectSession,
  onNewChat,
  onRenameSession,
  onDeleteSession,
}) => {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  if (!isOpen) return null;

  const startRename = (session: StudySession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const handleSaveRename = (sessionId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (editingTitle.trim() && onRenameSession) {
      onRenameSession(sessionId, editingTitle.trim());
    }
    setEditingSessionId(null);
  };

  const cancelRename = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setEditingSessionId(null);
  };

  return (
    <aside className="w-64 sm:w-72 border-r border-slate-200 bg-slate-50/70 flex flex-col min-h-0 h-full shrink-0">
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 text-sm font-medium transition-colors shadow-2xs"
        >
          <SquarePen className="w-4 h-4 text-slate-600" />
          <span>New chat</span>
        </button>
      </div>

      <div className="px-4 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
        History
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-0.5">
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs px-4">
            No previous chats yet. Start typing to begin a conversation.
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            const isEditing = session.id === editingSessionId;

            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer transition-colors ${
                  isActive
                    ? 'bg-slate-200/80 text-slate-900 font-medium'
                    : 'hover:bg-slate-200/50 text-slate-700'
                }`}
              >
                <div className="min-w-0 flex-1 flex items-center gap-2.5 mr-1">
                  <MessageSquare className="w-4 h-4 text-slate-400 shrink-0" />
                  {isEditing ? (
                    <div className="flex-1 flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveRename(session.id);
                          if (e.key === 'Escape') cancelRename();
                        }}
                        autoFocus
                        className="w-full text-xs font-medium px-2 py-1 border border-sky-400 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-sky-500"
                      />
                      <button
                        onClick={(e) => handleSaveRename(session.id, e)}
                        className="p-1 text-emerald-600 hover:bg-emerald-50 rounded"
                        title="Save"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => cancelRename(e)}
                        className="p-1 text-slate-400 hover:bg-slate-100 rounded"
                        title="Cancel"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <span className="text-sm truncate">{session.title}</span>
                  )}
                </div>

                {!isEditing && (
                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    {onRenameSession && (
                      <button
                        onClick={(e) => startRename(session, e)}
                        className="p-1 hover:bg-slate-300/60 text-slate-500 hover:text-slate-800 rounded-lg transition-colors"
                        title="Rename chat"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      className="p-1 hover:bg-rose-100 text-slate-500 hover:text-rose-600 rounded-lg transition-colors"
                      title="Delete chat"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
