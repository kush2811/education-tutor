import React from 'react';
import {
  GraduationCap,
  Activity,
  WifiOff,
  User as UserIcon,
  BookOpen,
  MessageSquare,
  LayoutDashboard,
  Home,
} from 'lucide-react';
import { HealthStatus, User } from '../types';

export type ActiveNavRoute = 'landing' | 'dashboard' | 'tutor' | 'curriculum';

interface HeaderProps {
  health: HealthStatus | null;
  loading: boolean;
  currentUser: User | null;
  activeRoute: ActiveNavRoute;
  onNavigate: (route: ActiveNavRoute) => void;
  onOpenProfile: () => void;
  onGoToLogin: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  loading,
  currentUser,
  activeRoute,
  onNavigate,
  onOpenProfile,
  onGoToLogin,
}) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-2xs shrink-0 z-30">
      <div className="flex items-center gap-4">
        {/* Brand Logo & Title */}
        <div
          onClick={() => onNavigate('landing')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-sky-600 text-white flex items-center justify-center shadow-md shadow-sky-100 group-hover:bg-sky-700 transition-colors">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight leading-none flex items-center gap-2">
              AI Student Tutor
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-700">
                Phase 2
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5">Socratic Problem Solver</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 ml-4 border-l border-slate-200 pl-4">
          <button
            onClick={() => onNavigate('landing')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeRoute === 'landing'
                ? 'bg-sky-50 text-sky-700 font-bold'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Home className="w-3.5 h-3.5" />
            Home
          </button>

          {currentUser && (
            <button
              onClick={() => onNavigate('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                activeRoute === 'dashboard'
                  ? 'bg-sky-50 text-sky-700 font-bold'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              Dashboard
            </button>
          )}

          <button
            onClick={() => onNavigate('tutor')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeRoute === 'tutor'
                ? 'bg-sky-50 text-sky-700 font-bold'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Tutor Chat
          </button>

          <button
            onClick={() => onNavigate('curriculum')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeRoute === 'curriculum'
                ? 'bg-sky-50 text-sky-700 font-bold'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Curriculum
          </button>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Health Badge */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border bg-slate-50">
          <Activity className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-500 text-[11px]">Backend:</span>
          {loading ? (
            <span className="text-slate-400 animate-pulse text-[11px]">Connecting...</span>
          ) : isHealthy ? (
            <span className="flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Healthy
            </span>
          ) : (
            <span className="flex items-center gap-1 text-rose-500 font-semibold text-[11px]">
              <WifiOff className="w-3 h-3" />
              Offline
            </span>
          )}
        </div>

        {/* User Auth Profile Trigger */}
        {currentUser ? (
          <button
            onClick={onOpenProfile}
            className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-xl hover:bg-slate-100 border border-slate-200 transition-colors text-left"
            title="View & Edit Profile"
          >
            <div className="w-7 h-7 rounded-lg bg-sky-600 text-white font-bold text-xs flex items-center justify-center">
              {currentUser.full_name ? currentUser.full_name.charAt(0).toUpperCase() : 'S'}
            </div>
            <div className="hidden sm:flex flex-col">
              <span className="text-xs font-bold text-slate-800 leading-tight">
                {currentUser.full_name}
              </span>
              <span className="text-[10px] text-slate-400 leading-tight">
                {currentUser.grade_level}
              </span>
            </div>
          </button>
        ) : (
          <button
            onClick={onGoToLogin}
            className="flex items-center gap-1.5 text-xs font-bold px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl shadow-xs transition-colors"
          >
            <UserIcon className="w-3.5 h-3.5" />
            Sign In
          </button>
        )}
      </div>
    </header>
  );
};
