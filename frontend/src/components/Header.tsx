import React from 'react';
import { GraduationCap, Activity, WifiOff, User as UserIcon, BookOpen, MessageSquare, LogOut } from 'lucide-react';
import { HealthStatus, User } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
  loading: boolean;
  currentUser: User | null;
  activeTab: 'chat' | 'curriculum';
  onTabChange: (tab: 'chat' | 'curriculum') => void;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  loading,
  currentUser,
  activeTab,
  onTabChange,
  onOpenAuth,
  onLogout,
}) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-sm shrink-0">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-sky-600 text-white flex items-center justify-center shadow-md shadow-sky-100">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 tracking-tight leading-none flex items-center gap-2">
              AI Multimodal Student Tutor
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-700">
                Phase 1 Foundation
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Socratic STEM Guidance • Multimodal Ingestion • Verifiable Knowledge
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="hidden md:flex items-center gap-1 ml-6 border-l border-slate-200 pl-6">
          <button
            onClick={() => onTabChange('chat')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'chat'
                ? 'bg-sky-50 text-sky-700 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Tutor Session
          </button>
          <button
            onClick={() => onTabChange('curriculum')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'curriculum'
                ? 'bg-sky-50 text-sky-700 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Curriculum & OER
          </button>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {/* API Health Pill */}
        <div className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border bg-slate-50">
          <Activity className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-500">API:</span>
          {loading ? (
            <span className="text-slate-400 animate-pulse text-[11px]">Checking...</span>
          ) : isHealthy ? (
            <span className="flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Connected
            </span>
          ) : (
            <span className="flex items-center gap-1 text-rose-500 font-semibold text-[11px]">
              <WifiOff className="w-3 h-3" />
              Offline
            </span>
          )}
        </div>

        {/* Auth / Profile Button */}
        {currentUser ? (
          <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
            <div className="flex flex-col text-right">
              <span className="text-xs font-bold text-slate-800 leading-tight">{currentUser.full_name}</span>
              <span className="text-[10px] text-slate-400">{currentUser.grade_level}</span>
            </div>
            <button
              onClick={onLogout}
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl shadow-xs transition-colors"
          >
            <UserIcon className="w-3.5 h-3.5" />
            Sign In
          </button>
        )}
      </div>
    </header>
  );
};
