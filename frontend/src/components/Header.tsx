import React from 'react';
import { GraduationCap, PanelLeft, LogIn } from 'lucide-react';
import { User } from '../types';

interface HeaderProps {
  currentUser: User | null;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  onNewChat: () => void;
  onOpenProfile: () => void;
  onGoToLogin: () => void;
  onGoToRegister: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  isSidebarOpen,
  onToggleSidebar,
  onNewChat,
  onOpenProfile,
  onGoToLogin,
  onGoToRegister,
}) => {
  return (
    <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between shrink-0 z-30">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
          title={isSidebarOpen ? 'Hide chat history' : 'Show chat history'}
        >
          <PanelLeft className="w-5 h-5" />
        </button>

        <button
          onClick={onNewChat}
          className="flex items-center gap-2.5 text-left group"
          title="New chat"
        >
          <div className="w-8 h-8 rounded-lg bg-sky-600 text-white flex items-center justify-center group-hover:bg-sky-700 transition-colors">
            <GraduationCap className="w-4 h-4" />
          </div>
          <span className="text-base font-semibold text-slate-900 tracking-tight">
            AI Tutor
          </span>
        </button>
      </div>

      <div className="flex items-center gap-2">
        {currentUser ? (
          <button
            onClick={onOpenProfile}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-full hover:bg-slate-100 border border-slate-200 transition-colors"
            title="Account & Preferences"
          >
            <div className="w-7 h-7 rounded-full bg-sky-600 text-white font-semibold text-xs flex items-center justify-center">
              {currentUser.full_name ? currentUser.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <span className="hidden sm:inline text-xs font-medium text-slate-800 pr-1">
              {currentUser.full_name}
            </span>
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={onGoToLogin}
              className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-full transition-colors"
            >
              <LogIn className="w-3.5 h-3.5" />
              Log in
            </button>
            <button
              onClick={onGoToRegister}
              className="hidden sm:inline-flex items-center text-xs font-semibold px-3.5 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-full transition-colors"
            >
              Sign up
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
