import React, { useState } from 'react';
import { Plus, BookOpen, Trash2, Clock } from 'lucide-react';
import { StudySession } from '../types';

interface SessionListProps {
  sessions: StudySession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: (title: string, subject: string) => void;
  onDeleteSession: (id: string) => void;
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}) => {
  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newSubject, setNewSubject] = useState('Mathematics');

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    onCreateSession(newTitle.trim(), newSubject);
    setNewTitle('');
    setShowModal(false);
  };

  return (
    <aside className="w-80 border-r border-slate-200 bg-white flex flex-col h-full">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <h2 className="font-semibold text-slate-800 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-sky-600" />
          Study Sessions
        </h2>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1 text-xs font-medium px-2.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-700 text-white transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs px-4">
            No study sessions yet. Click "New" to start a guided tutoring session!
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${
                  isActive
                    ? 'bg-sky-50 border border-sky-200 text-sky-900 shadow-sm'
                    : 'hover:bg-slate-50 text-slate-700 border border-transparent'
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                      {session.subject}
                    </span>
                  </div>
                  <h3 className="font-medium text-sm truncate mt-1 text-slate-800">
                    {session.title}
                  </h3>
                  <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(session.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <span>• {session.messages?.length || 0} messages</span>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Are you sure you want to delete this study session?')) {
                      onDeleteSession(session.id);
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded-lg transition-all"
                  title="Delete Session"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Modal for creating a new session */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl border border-slate-100 animate-in fade-in zoom-in-95 duration-150">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Start New Tutoring Session</h3>
            <p className="text-xs text-slate-500 mb-4">Set your study topic to guide the AI tutor's Socratic approach.</p>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Subject</label>
                <select
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="Mathematics">Mathematics & Calculus</option>
                  <option value="Physics">Physics & Mechanics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Computer Science">Computer Science & Algorithms</option>
                  <option value="General STEM">General STEM</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Session Goal / Topic</label>
                <input
                  type="text"
                  placeholder="e.g. Solving Quadratic Equations with the Quadratic Formula"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  className="w-full text-sm border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-medium bg-sky-600 hover:bg-sky-700 text-white rounded-xl shadow-sm transition-colors"
                >
                  Create Session
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  );
};
