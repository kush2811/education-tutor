import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  MessageSquare,
  UploadCloud,
  PenTool,
  Flame,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  Plus,
} from 'lucide-react';
import { api } from '../services/api';
import { DashboardStats, User } from '../types';

interface StudentDashboardProps {
  currentUser: User | null;
  onStartSession: (topic?: string, subject?: string) => void;
  onResumeSession: (sessionId: string) => void;
  onOpenUpload: () => void;
  onOpenCurriculum: () => void;
  onOpenScratchpad: () => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  currentUser,
  onStartSession,
  onResumeSession,
  onOpenUpload,
  onOpenCurriculum,
  onOpenScratchpad,
}) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getDashboardStats();
        setStats(data);
      } catch (err) {
        console.warn('Could not load dynamic dashboard statistics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [currentUser]);

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 p-6 sm:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-sky-600 via-sky-700 to-indigo-700 rounded-3xl p-6 sm:p-8 text-white shadow-xl shadow-sky-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-xs text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Personalized Socratic Learning Hub</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome back, {currentUser?.full_name || 'Student Learner'}!
            </h2>
            <p className="text-xs sm:text-sm text-sky-100 mt-1 max-w-xl leading-relaxed">
              Academic Track: <span className="font-semibold text-white">{currentUser?.grade_level || 'Grade 10'}</span>.
              Ready to work through today's STEM problems with guided hints and verified calculations?
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => onStartSession()}
              className="px-5 py-3 bg-white hover:bg-sky-50 text-sky-800 font-bold text-xs sm:text-sm rounded-2xl shadow-lg transition-all flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Tutoring Session
            </button>
            <button
              onClick={onOpenUpload}
              className="px-4 py-3 bg-white/10 hover:bg-white/20 text-white font-semibold text-xs sm:text-sm rounded-2xl border border-white/20 transition-all flex items-center gap-2"
            >
              <UploadCloud className="w-4 h-4" />
              Upload Worksheet
            </button>
          </div>
        </div>

        {/* Metrics Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Study Sessions</span>
              <div className="w-8 h-8 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
                <MessageSquare className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-3">
              {loading ? '-' : stats?.total_sessions || 0}
            </div>
            <span className="text-[11px] text-slate-400 mt-0.5 block">Active conversations</span>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Exchanges</span>
              <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <FileText className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-3">
              {loading ? '-' : stats?.total_messages || 0}
            </div>
            <span className="text-[11px] text-slate-400 mt-0.5 block">Socratic dialogue steps</span>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Uploaded Assets</span>
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <UploadCloud className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-3">
              {loading ? '-' : stats?.total_uploads || 0}
            </div>
            <span className="text-[11px] text-slate-400 mt-0.5 block">Diagrams & worksheets</span>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Learning Streak</span>
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                <Flame className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-3 flex items-center gap-1.5">
              <span>{loading ? '-' : stats?.active_streak_days || 1}</span>
              <span className="text-xs font-normal text-slate-400">days</span>
            </div>
            <span className="text-[11px] text-slate-400 mt-0.5 block">Consistent practice</span>
          </div>
        </div>

        {/* Quick Launch Action Cards */}
        <div>
          <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3">
            Quick Learning Shortcuts
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <button
              onClick={() => onStartSession()}
              className="group p-5 bg-white rounded-2xl border border-slate-200 hover:border-sky-300 hover:shadow-md transition-all text-left flex items-start gap-4"
            >
              <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-800">Ask a Question</h4>
                <p className="text-xs text-slate-500 mt-0.5">Start step-by-step Socratic guided problem solving.</p>
              </div>
            </button>

            <button
              onClick={onOpenCurriculum}
              className="group p-5 bg-white rounded-2xl border border-slate-200 hover:border-sky-300 hover:shadow-md transition-all text-left flex items-start gap-4"
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-800">Browse Curriculum</h4>
                <p className="text-xs text-slate-500 mt-0.5">Explore official NCERT & OpenStax textbook resources.</p>
              </div>
            </button>

            <button
              onClick={onOpenScratchpad}
              className="group p-5 bg-white rounded-2xl border border-slate-200 hover:border-sky-300 hover:shadow-md transition-all text-left flex items-start gap-4"
            >
              <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                <PenTool className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-800">Interactive Scratchpad</h4>
                <p className="text-xs text-slate-500 mt-0.5">Draw diagrams, write equations, and export work.</p>
              </div>
            </button>
          </div>
        </div>

        {/* Content Section: Recent Sessions */}
        <div className="w-full bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-600" />
              Recent Tutoring Sessions
            </h3>
            <button
              onClick={() => onStartSession()}
              className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
            >
              <span>New Session</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-400">Loading your sessions...</div>
          ) : !stats?.recent_sessions || stats.recent_sessions.length === 0 ? (
            <div className="py-12 text-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-semibold text-slate-700">No sessions yet</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                Start your first guided tutoring session to practice STEM problem solving.
              </p>
              <button
                onClick={() => onStartSession()}
                className="mt-4 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold transition-colors"
              >
                Start First Session
              </button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {stats.recent_sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => onResumeSession(s.id)}
                  className="py-3.5 flex items-center justify-between hover:bg-slate-50/70 rounded-xl px-3 -mx-3 cursor-pointer transition-colors group"
                >
                  <div className="min-w-0 flex-1 pr-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                        {s.subject}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(s.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h4 className="font-semibold text-sm text-slate-800 truncate group-hover:text-sky-600 transition-colors">
                      {s.title}
                    </h4>
                    <span className="text-[11px] text-slate-400">
                      {s.message_count} messages exchanged
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs font-semibold text-sky-600 group-hover:translate-x-1 transition-transform">
                      Resume &rarr;
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

