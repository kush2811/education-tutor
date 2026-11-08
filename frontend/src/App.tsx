import React, { useState, useEffect } from 'react';
import { Header, ActiveNavRoute } from './components/Header';
import { SessionList } from './components/SessionList';
import { ChatInterface } from './components/ChatInterface';
import { WhiteboardCanvas } from './components/WhiteboardCanvas';
import { CurriculumView } from './components/CurriculumView';
import { FileUploadModal } from './components/FileUploadModal';
import { ProfileModal } from './components/ProfileModal';
import { VoicePlayer } from './components/VoicePlayer';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { StudentDashboard } from './pages/StudentDashboard';
import { api, tokenStorage } from './services/api';
import { HealthStatus, StudySession, User, UploadedFileResponse } from './types';
import { PenTool } from 'lucide-react';

export const App: React.FC = () => {
  // Navigation & Route state
  const [currentRoute, setCurrentRoute] = useState<ActiveNavRoute | 'login' | 'register'>('landing');

  // Backend Health
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);

  // Authentication State
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [showProfileModal, setShowProfileModal] = useState(false);

  // Sessions & Chat State
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<StudySession | null>(null);

  // Modals & Sidebars
  const [showWhiteboard, setShowWhiteboard] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Voice Player Dock State
  const [activeVoiceText, setActiveVoiceText] = useState<string | null>(null);

  // Check backend health
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await api.getHealth();
        setHealth(res);
      } catch (err) {
        console.warn('Backend offline or unreachable:', err);
        setHealth(null);
      } finally {
        setLoadingHealth(false);
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  // Restore authenticated session from localStorage
  useEffect(() => {
    const verifyUser = async () => {
      const token = tokenStorage.get();
      if (!token) return;
      try {
        const user = await api.getMe();
        setCurrentUser(user);
      } catch (err) {
        console.info('Session token expired, clearing.');
        tokenStorage.clear();
        setCurrentUser(null);
      }
    };
    verifyUser();
  }, []);

  // Load study sessions
  const loadSessions = async () => {
    try {
      const data = await api.listSessions(currentUser?.id || 'default_student');
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
  }, [currentUser]);

  // Load active session messages
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
        console.error('Failed to load session details:', err);
      }
    };
    fetchActive();
  }, [activeSessionId]);

  // Handlers for session lifecycle
  const handleCreateSession = async (title?: string, subject = 'Mathematics') => {
    try {
      const sessionTitle = title || `Practice: ${subject} Problem Solving`;
      const newSession = await api.createSession({
        title: sessionTitle,
        subject,
        student_id: currentUser?.id || 'default_student',
      });
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setActiveSession(newSession);
      setCurrentRoute('tutor');
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

  const handleRenameSession = async (id: string, newTitle: string) => {
    try {
      const updated = await api.updateSession(id, { title: newTitle });
      setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title: updated.title } : s)));
      if (activeSession && activeSession.id === id) {
        setActiveSession((prev) => (prev ? { ...prev, title: updated.title } : prev));
      }
    } catch (err) {
      console.error('Failed to rename session:', err);
    }
  };

  const handleSendMessage = async (content: string, contentType = 'text') => {
    if (!activeSessionId) return;
    try {
      const userMsg = await api.addMessage(activeSessionId, {
        sender_role: 'user',
        content,
        content_type: contentType,
      });

      setActiveSession((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          messages: [...prev.messages, userMsg],
        };
      });

      // Socratic baseline response
      setTimeout(async () => {
        try {
          const tutorMsg = await api.addMessage(activeSessionId, {
            sender_role: 'assistant',
            content: `### Socratic Problem Guidance\n\nI received your inquiry:\n> ${content}\n\nLet's break this down systematically:\n\n1. What is the fundamental concept or theorem governing this problem?\n2. What variables or parameters are explicitly given in the problem statement?\n\nTake a moment to formulate your initial hypothesis: what formula would you apply first?`,
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
          console.error('Tutor response failed:', e);
        }
      }, 500);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleUploadSuccess = (uploaded: UploadedFileResponse) => {
    if (!activeSessionId) return;
    handleSendMessage(
      `[Uploaded ${uploaded.file_type.toUpperCase()}: ${uploaded.file_name} (${(uploaded.file_size / 1024).toFixed(1)} KB)]\nPlease analyze this document and guide me step-by-step.`,
      uploaded.file_type
    );
  };

  const handleLogout = () => {
    tokenStorage.clear();
    setCurrentUser(null);
    setShowProfileModal(false);
    setCurrentRoute('landing');
  };

  // Render Page Content based on route
  const renderMainContent = () => {
    if (currentRoute === 'landing') {
      return (
        <LandingPage
          onStartLearning={() => {
            if (currentUser) {
              setCurrentRoute('dashboard');
            } else {
              setCurrentRoute('register');
            }
          }}
          onLoginClick={() => setCurrentRoute('login')}
          onExploreCurriculum={() => setCurrentRoute('curriculum')}
        />
      );
    }

    if (currentRoute === 'login') {
      return (
        <LoginPage
          onLoginSuccess={(user) => {
            setCurrentUser(user);
            setCurrentRoute('dashboard');
          }}
          onGoToRegister={() => setCurrentRoute('register')}
          onGoHome={() => setCurrentRoute('landing')}
        />
      );
    }

    if (currentRoute === 'register') {
      return (
        <RegisterPage
          onRegisterSuccess={(user) => {
            setCurrentUser(user);
            setCurrentRoute('dashboard');
          }}
          onGoToLogin={() => setCurrentRoute('login')}
          onGoHome={() => setCurrentRoute('landing')}
        />
      );
    }

    if (currentRoute === 'dashboard') {
      return (
        <StudentDashboard
          currentUser={currentUser}
          onStartSession={(topic, subject) => handleCreateSession(topic, subject)}
          onResumeSession={(id) => {
            setActiveSessionId(id);
            setCurrentRoute('tutor');
          }}
          onOpenUpload={() => setShowUploadModal(true)}
          onOpenCurriculum={() => setCurrentRoute('curriculum')}
          onOpenScratchpad={() => {
            setCurrentRoute('tutor');
            setShowWhiteboard(true);
          }}
        />
      );
    }

    if (currentRoute === 'curriculum') {
      return <CurriculumView />;
    }

    // Main 'tutor' chat interface
    return (
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Study Sessions Sidebar */}
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onCreateSession={handleCreateSession}
          onRenameSession={handleRenameSession}
          onDeleteSession={handleDeleteSession}
        />

        {/* Center: Main Chat Stream */}
        <main className="flex-1 flex flex-col relative overflow-hidden">
          <ChatInterface
            session={activeSession}
            onSendMessage={handleSendMessage}
            onOpenUpload={() => setShowUploadModal(true)}
            onPlayVoice={(text) => setActiveVoiceText(text)}
          />

          {/* Voice Interface Dock (if active) */}
          {activeVoiceText && (
            <VoicePlayer
              textToSpeak={activeVoiceText}
              onClose={() => setActiveVoiceText(null)}
            />
          )}
        </main>

        {/* Right Whiteboard Toggle & Panel */}
        <div
          className={`transition-all duration-300 ease-in-out border-l border-slate-200 bg-white flex flex-col ${
            showWhiteboard ? 'w-[480px]' : 'w-12 items-center'
          }`}
        >
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
    );
  };

  return (
    <div className="flex flex-col h-screen bg-slate-100">
      {/* Top Header Navigation (hidden on standalone login/register pages for clean focus) */}
      {currentRoute !== 'login' && currentRoute !== 'register' && (
        <Header
          health={health}
          loading={loadingHealth}
          currentUser={currentUser}
          activeRoute={currentRoute as ActiveNavRoute}
          onNavigate={(route) => {
            if (route === 'dashboard' && !currentUser) {
              setCurrentRoute('login');
            } else {
              setCurrentRoute(route);
            }
          }}
          onOpenProfile={() => setShowProfileModal(true)}
          onGoToLogin={() => setCurrentRoute('login')}
        />
      )}

      {/* Main Content Area */}
      {renderMainContent()}

      {/* Profile Modal */}
      <ProfileModal
        isOpen={showProfileModal}
        user={currentUser}
        onClose={() => setShowProfileModal(false)}
        onProfileUpdated={(updated) => setCurrentUser(updated)}
        onLogout={handleLogout}
      />

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={showUploadModal}
        sessionId={activeSessionId || undefined}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
};

export default App;
