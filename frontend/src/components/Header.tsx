import React from 'react';
import { GraduationCap, Activity, WifiOff } from 'lucide-react';
import { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, loading }) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center shadow-md shadow-sky-100">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            AI Multimodal Student Tutor
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-700">
              v0.1.0 Architecture Baseline
            </span>
          </h1>
          <p className="text-xs text-slate-500">
            Socratic Problem Solver • Multimodal Vision • Voice Interaction • SymPy Verified
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-lg border bg-slate-50">
          <Activity className="w-4 h-4 text-slate-400" />
          <span>API Backend:</span>
          {loading ? (
            <span className="text-slate-400 animate-pulse">Checking...</span>
          ) : isHealthy ? (
            <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Connected (SQLite ready)
            </span>
          ) : (
            <span className="flex items-center gap-1 text-rose-500 font-semibold">
              <WifiOff className="w-3.5 h-3.5" />
              Offline
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
