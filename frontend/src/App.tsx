import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { SessionList } from './components/SessionList';
import { ChatInterface } from './components/ChatInterface';
import { WhiteboardCanvas } from './components/WhiteboardCanvas';
import { api } from './services/api';
import { HealthStatus, StudySession } from './types';
import { PenTool } from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<StudySession | null>(null);
  const [showWhiteboard, setShowWhiteboard] = useState(false);

  // Poll or check health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await api.getHealth();
        setHealth(res);
      } catch (err) {
        console.warn('Backend currently unreachable:', err);
        setHealth(null);
      } finally {
        setLoadingHealth(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  // Load sessions
  const loadSessions = async () => {
    try {
      const data = await api.listSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
      }
    } catch (err) {
      console.warn('Could not load sessions:', err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  // Fetch full active session details when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setActiveSession(null);
      return;
    }
    const fetchActive = async () => {
      try {
        const data = await api.getSession(activeSessionId);
        setActiveSession(data);
      } catch (err) {
        console.error('Failed to load active session:', err);
      }
    };
    fetchActive();
  }, [activeSessionId]);

  const handleCreateSession = async (title: string, subject: string) => {
    try {
      const newSession = await api.createSession({ title, subject });
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setActiveSession(newSession);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleDeleteSession = async (id: string) => {
    try {
      await api.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setActiveSession(null);
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSendMessage = async (content: string, contentType = 'text') => {
    if (!activeSessionId) return;
    try {
      // 1. Post user message
      const userMsg = await api.addMessage(activeSessionId, {
        sender_role: 'user',
        content,
        content_type: contentType,
      });

      // Update UI optimistically
      setActiveSession((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          messages: [...prev.messages, userMsg],
        };
      });

      // 2. Baseline Mock/Socratic Echo response (will be replaced by full Gemini/AI engine in Phase 3)
      setTimeout(async () => {
        try {
          const tutorMsg = await api.addMessage(activeSessionId, {
            sender_role: 'assistant',
            content: `Hello! I received your inquiry: "${content}".\n\nLet's analyze this step by step. What fundamental concept or equation do you think applies first here?`,
            content_type: 'text',
          });

          setActiveSession((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              messages: [...prev.messages, tutorMsg],
            };
          });
        } catch (e) {
          console.error('Tutor response recording failed:', e);
        }
      }, 600);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-100">
      <Header health={health} loading={loadingHealth} />

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Study Sessions Sidebar */}
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onCreateSession={handleCreateSession}
          onDeleteSession={handleDeleteSession}
        />

        {/* Center: Main Chat & Tutor Interface */}
        <main className="flex-1 flex flex-col relative overflow-hidden">
          <ChatInterface
            session={activeSession}
            onSendMessage={handleSendMessage}
          />
        </main>

        {/* Right Whiteboard Toggle & Panel */}
        <div className={`transition-all duration-300 ease-in-out border-l border-slate-200 bg-white flex flex-col ${
          showWhiteboard ? 'w-[480px]' : 'w-12 items-center'
        }`}>
          <div className="p-2 border-b border-slate-200 w-full flex items-center justify-between bg-slate-50">
            <button
              onClick={() => setShowWhiteboard(!showWhiteboard)}
              className="p-2 text-slate-600 hover:text-sky-600 hover:bg-slate-200 rounded-xl transition-colors flex items-center gap-2 text-xs font-semibold"
              title={showWhiteboard ? 'Collapse Scratchpad' : 'Open Scratchpad & Whiteboard'}
            >
              <PenTool className="w-4 h-4 text-sky-600" />
              {showWhiteboard && <span>Interactive Scratchpad</span>}
            </button>
          </div>

          {showWhiteboard && (
            <div className="flex-1 p-3 overflow-hidden">
              <WhiteboardCanvas />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
