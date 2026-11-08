import React from 'react';
import {
  GraduationCap,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Volume2,
  FileText,
  CheckCircle2,
  BookOpen,
  PenTool,
} from 'lucide-react';
import { MathRenderer } from '../components/MathRenderer';

interface LandingPageProps {
  onStartLearning: () => void;
  onLoginClick: () => void;
  onExploreCurriculum: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartLearning,
  onLoginClick,
  onExploreCurriculum,
}) => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col selection:bg-sky-100 selection:text-sky-900">
      {/* Navigation Bar */}
      <header className="bg-white border-b border-slate-200/80 sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-sky-600 text-white flex items-center justify-center shadow-lg shadow-sky-100">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 leading-none">
              AI Multimodal Student Tutor
            </h1>
            <p className="text-[11px] text-slate-500 mt-0.5">Socratic STEM Guidance & Problem Solver</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onExploreCurriculum}
            className="hidden sm:flex items-center gap-1.5 text-xs font-semibold px-3 py-2 text-slate-600 hover:text-sky-600 hover:bg-slate-100 rounded-xl transition-colors"
          >
            <BookOpen className="w-4 h-4" />
            Curriculum (NCERT & OER)
          </button>
          <button
            onClick={onLoginClick}
            className="text-xs font-semibold px-4 py-2 text-slate-700 hover:text-sky-600 hover:bg-slate-100 rounded-xl transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={onStartLearning}
            className="flex items-center gap-1.5 text-xs font-bold px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl shadow-md shadow-sky-100 transition-all"
          >
            Get Started
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="max-w-5xl mx-auto px-6 pt-16 pb-12 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sky-100/70 border border-sky-200 text-sky-800 text-xs font-semibold mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <Sparkles className="w-4 h-4 text-sky-600" />
            <span>Next-Generation Socratic Learning Platform</span>
          </div>

          <h2 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight max-w-3xl mx-auto">
            Master Complex STEM Problems <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-600 to-indigo-600">
              Without Getting Answer-Dumped.
            </span>
          </h2>

          <p className="mt-5 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Generic chatbots hand you the answer. Our multimodal tutor guides you step-by-step using the
            <strong> Socratic method</strong>, verifies every calculation with symbolic math, and turns handwritten notes into verified solutions.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={onStartLearning}
              className="px-6 py-3.5 bg-sky-600 hover:bg-sky-700 text-white rounded-2xl font-bold text-sm shadow-xl shadow-sky-200 hover:shadow-2xl hover:shadow-sky-300 transition-all flex items-center gap-2"
            >
              Start Free Guided Tutoring
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onExploreCurriculum}
              className="px-6 py-3.5 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-2xl font-semibold text-sm shadow-xs transition-all flex items-center gap-2"
            >
              <BookOpen className="w-4 h-4 text-sky-600" />
              Explore Curriculum Standards
            </button>
          </div>

          {/* Interactive Preview Card */}
          <div className="mt-12 bg-white rounded-3xl border border-slate-200 shadow-xl p-6 max-w-3xl mx-auto text-left">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-rose-400" />
                <span className="w-3 h-3 rounded-full bg-amber-400" />
                <span className="w-3 h-3 rounded-full bg-emerald-400" />
                <span className="text-xs font-semibold text-slate-500 ml-2">Live Socratic Tutor Session</span>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                SymPy Verified
              </span>
            </div>

            <div className="space-y-4 text-sm">
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/60">
                <div className="text-xs font-bold text-slate-500 mb-1">Student Problem (Handwritten or Typed):</div>
                <div className="text-slate-800 font-medium">
                  Find the roots of <MathRenderer math="2x^2 - 8x + 6 = 0" /> using factorization or the quadratic formula.
                </div>
              </div>

              <div className="bg-sky-50/70 p-4 rounded-2xl border border-sky-100">
                <div className="flex items-center gap-2 text-xs font-bold text-sky-800 mb-1">
                  <Sparkles className="w-3.5 h-3.5 text-sky-600" />
                  <span>AI Tutor (Socratic Prompt - Tier 2):</span>
                </div>
                <p className="text-slate-700 text-xs sm:text-sm leading-relaxed">
                  Notice that all terms in <MathRenderer math="2x^2 - 8x + 6 = 0" /> share a common factor of 2.
                  What happens when you divide the entire equation by 2?
                </p>
                <div className="mt-3 p-3 bg-white rounded-xl border border-sky-100 text-xs text-slate-600">
                  <span className="font-semibold text-sky-700">Formula Hint: </span>
                  Recall the quadratic formula <MathRenderer math="x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}" /> where <MathRenderer math="a=1, b=-4, c=3" />.
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Grid */}
        <section className="bg-white border-t border-slate-200 py-16 px-6">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <h3 className="text-xs font-bold uppercase tracking-wider text-sky-600">Built for Authentic Learning</h3>
              <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-1">
                Everything you need to master mathematics & science
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-sky-200 transition-all">
                <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center mb-4">
                  <FileText className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-base text-slate-900 mb-1">Multimodal Ingestion</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Upload photos of handwritten calculations, PDF worksheets, or textbook geometry figures. Our vision pipeline extracts clean LaTeX.
                </p>
              </div>

              <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-sky-200 transition-all">
                <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4">
                  <Cpu className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-base text-slate-900 mb-1">Deterministic Math Verification</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  No arithmetic hallucinations. Derivations and polynomial roots are verified programmatically with SymPy before display.
                </p>
              </div>

              <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-sky-200 transition-all">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4">
                  <Volume2 className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-base text-slate-900 mb-1">Synchronized Voice & Subtitles</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Hear explanations spoken naturally with synchronized karaoke-style word highlighting, variable speed, and replay controls.
                </p>
              </div>

              <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-sky-200 transition-all">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center mb-4">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-base text-slate-900 mb-1">Curriculum Grounded (OER)</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Every conceptual explanation is grounded in official public curricula (NCERT, OpenStax) with verifiable chapter and page citations.
                </p>
              </div>

              <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-sky-200 transition-all">
                <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center mb-4">
                  <PenTool className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-base text-slate-900 mb-1">Interactive Whiteboard</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Scratch calculations, draw free-body diagrams, and export notes directly into your tutoring conversation stream.
                </p>
              </div>

              <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-sky-200 transition-all">
                <div className="w-10 h-10 rounded-xl bg-violet-100 text-violet-600 flex items-center justify-center mb-4">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-base text-slate-900 mb-1">Student Mastery Tracking</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Identify recurring misconceptions, monitor topic strengths, and track your study streak across multiple sessions.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 px-6 py-8 text-center text-xs text-slate-400">
        <p>© 2026 AI-Powered Multimodal Student Tutor & Problem Solver. Built with modern Socratic AI & Open Educational Resources.</p>
      </footer>
    </div>
  );
};

