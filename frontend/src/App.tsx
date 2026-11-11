import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { SessionList } from './components/SessionList';
import { ChatInterface } from './components/ChatInterface';
import { ProfileModal } from './components/ProfileModal';
import { VoicePlayer } from './components/VoicePlayer';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { api, tokenStorage } from './services/api';
import { StudySession, User } from './types';

type AppRoute = 'tutor' | 'login' | 'register';

export const App: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState<AppRoute>('tutor');

  // Authentication State
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [showProfileModal, setShowProfileModal] = useState(false);

  // Chat History & Active Chat State
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<StudySession | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Voice Player Dock State (triggered on-demand via "Listen")
  const [activeVoiceText, setActiveVoiceText] = useState<string | null>(null);

  // Restore authenticated session from localStorage
  useEffect(() => {
    const verifyUser = async () => {
      const token = tokenStorage.get();
      if (!token) return;
      try {
        const user = await api.getMe();
        setCurrentUser(user);
      } catch {
        tokenStorage.clear();
        setCurrentUser(null);
      }
    };
    verifyUser();
  }, []);

  // Load chat history whenever authentication state changes
  const loadSessions = async () => {
    try {
      const data = await api.listSessions(currentUser?.id || 'default_student');
      setSessions(data);
    } catch (err) {
      console.warn('Could not load chat history:', err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [currentUser]);

  // Load selected chat messages
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
        console.error('Failed to load chat details:', err);
      }
    };
    fetchActive();
  }, [activeSessionId]);

  const handleNewChat = () => {
    setActiveSessionId(null);
    setActiveSession(null);
    setActiveVoiceText(null);
    setCurrentRoute('tutor');
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
      console.error('Failed to delete chat:', err);
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
      console.error('Failed to rename chat:', err);
    }
  };

  const handleSendMessage = async (
    content: string,
    contentType = 'text',
    attachedFile?: File
  ) => {
    let targetSessionId = activeSessionId;

    // Auto-create a new chat session seamlessly on first message
    if (!targetSessionId) {
      const rawTitle = attachedFile
        ? attachedFile.name
        : content.replace(/\s+/g, ' ').trim();
      const chatTitle =
        rawTitle.length > 42 ? `${rawTitle.slice(0, 42)}...` : rawTitle || 'New Chat';

      const created = await api.createSession({
        title: chatTitle,
        subject: 'General STEM',
        student_id: currentUser?.id || 'default_student',
      });
      targetSessionId = created.id;
      setSessions((prev) => [created, ...prev]);
      setActiveSessionId(created.id);
      setActiveSession(created);
    }

    if (attachedFile) {
      await api.executePipelineFile(attachedFile, {
        session_id: targetSessionId,
        level: currentUser?.preferred_explanation_level || 'intermediate',
        preferred_voice: currentUser?.preferred_voice || 'en-US-AriaNeural',
        playback_speed: currentUser?.preferred_playback_speed || 1.0,
        synthesize_voice: false,
      });
    } else {
      await api.executePipeline({
        query: content,
        session_id: targetSessionId,
        level: currentUser?.preferred_explanation_level || 'intermediate',
        preferred_voice: currentUser?.preferred_voice || 'en-US-AriaNeural',
        playback_speed: currentUser?.preferred_playback_speed || 1.0,
        synthesize_voice: false,
        input_type: contentType,
      });
    }

    const updatedSession = await api.getSession(targetSessionId);
    setActiveSession(updatedSession);
    setSessions((prev) => {
      const exists = prev.some((s) => s.id === updatedSession.id);
      const updatedList = exists
        ? prev.map((s) => (s.id === updatedSession.id ? updatedSession : s))
        : [updatedSession, ...prev];
      return updatedList;
    });
  };

  const handleLogout = () => {
    tokenStorage.clear();
    setCurrentUser(null);
    setShowProfileModal(false);
    setActiveSessionId(null);
    setActiveSession(null);
    setActiveVoiceText(null);
    setCurrentRoute('tutor');
  };

  if (currentRoute === 'login') {
    return (
      <LoginPage
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          setActiveSessionId(null);
          setActiveSession(null);
          setCurrentRoute('tutor');
        }}
        onGoToRegister={() => setCurrentRoute('register')}
        onGoHome={() => setCurrentRoute('tutor')}
      />
    );
  }

  if (currentRoute === 'register') {
    return (
      <RegisterPage
        onRegisterSuccess={(user) => {
          setCurrentUser(user);
          setActiveSessionId(null);
          setActiveSession(null);
          setCurrentRoute('tutor');
        }}
        onGoToLogin={() => setCurrentRoute('login')}
        onGoHome={() => setCurrentRoute('tutor')}
      />
    );
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Single Minimal Header */}
      <Header
        currentUser={currentUser}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        onNewChat={handleNewChat}
        onOpenProfile={() => setShowProfileModal(true)}
        onGoToLogin={() => setCurrentRoute('login')}
        onGoToRegister={() => setCurrentRoute('register')}
      />

      {/* ChatGPT-style Workspace: History Sidebar + Direct Chat */}
      <div className="flex-1 flex overflow-hidden">
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          isOpen={isSidebarOpen}
          onSelectSession={(id) => {
            setActiveSessionId(id);
            setActiveVoiceText(null);
          }}
          onNewChat={handleNewChat}
          onRenameSession={handleRenameSession}
          onDeleteSession={handleDeleteSession}
        />

        <main className="flex-1 flex flex-col relative overflow-hidden">
          <ChatInterface
            session={activeSession}
            onSendMessage={handleSendMessage}
            onPlayVoice={(text) => setActiveVoiceText(text)}
          />

          {activeVoiceText && (
            <VoicePlayer
              textToSpeak={activeVoiceText}
              onClose={() => setActiveVoiceText(null)}
            />
          )}
        </main>
      </div>

      {/* Account & Preferences Modal */}
      <ProfileModal
        isOpen={showProfileModal}
        user={currentUser}
        onClose={() => setShowProfileModal(false)}
        onProfileUpdated={(updated) => setCurrentUser(updated)}
        onLogout={handleLogout}
      />
    </div>
  );
};

export default App;
