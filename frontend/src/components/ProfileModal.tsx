import React, { useState, useEffect } from 'react';
import {
  User as UserIcon,
  GraduationCap,
  Calendar,
  X,
  Check,
  LogOut,
  AlertCircle,
  Sliders,
  Volume2,
  Gauge,
  Languages,
  BookOpen,
} from 'lucide-react';
import { api } from '../services/api';
import { User, StudentPreferences } from '../types';

interface ProfileModalProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
  onProfileUpdated: (updated: User) => void;
  onLogout: () => void;
}

const AVAILABLE_VOICES = [
  { id: 'en-US-AriaNeural', label: 'Aria (Female - Natural, Warm)' },
  { id: 'en-US-GuyNeural', label: 'Guy (Male - Clear, Friendly)' },
  { id: 'en-US-JennyNeural', label: 'Jenny (Female - Conversational)' },
  { id: 'en-US-ChristopherNeural', label: 'Christopher (Male - Authoritative)' },
];

const SPEED_OPTIONS = [0.75, 1.0, 1.25, 1.5, 2.0];

const LANGUAGE_OPTIONS = [
  { id: 'en', label: 'English (US / Global)' },
  { id: 'es', label: 'Spanish (Español)' },
  { id: 'fr', label: 'French (Français)' },
  { id: 'de', label: 'German (Deutsch)' },
  { id: 'hi', label: 'Hindi (हिन्दी)' },
];

const SUBJECT_OPTIONS = [
  'Mathematics',
  'Physics',
  'Chemistry',
  'Computer Science',
  'Biology',
];

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  user,
  onClose,
  onProfileUpdated,
  onLogout,
}) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences'>('profile');

  // Profile Fields
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [gradeLevel, setGradeLevel] = useState(user?.grade_level || 'Grade 10');

  // Preferences Fields
  const [explanationLevel, setExplanationLevel] = useState<'beginner' | 'intermediate' | 'advanced'>(
    (user?.preferred_explanation_level as any) || 'intermediate'
  );
  const [preferredVoice, setPreferredVoice] = useState(user?.preferred_voice || 'en-US-AriaNeural');
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(user?.preferred_playback_speed || 1.0);
  const [language, setLanguage] = useState(user?.preferred_language || 'en');
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>(() => {
    if (user?.preferred_subjects) {
      return user.preferred_subjects.split(',').map((s) => s.trim()).filter(Boolean);
    }
    return ['Mathematics', 'Physics', 'Computer Science'];
  });

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync state whenever user prop updates or modal opens
  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setGradeLevel(user.grade_level || 'Grade 10');
      if (user.preferred_explanation_level) {
        setExplanationLevel(user.preferred_explanation_level as any);
      }
      if (user.preferred_voice) {
        setPreferredVoice(user.preferred_voice);
      }
      if (user.preferred_playback_speed) {
        setPlaybackSpeed(user.preferred_playback_speed);
      }
      if (user.preferred_language) {
        setLanguage(user.preferred_language);
      }
      if (user.preferred_subjects) {
        setSelectedSubjects(user.preferred_subjects.split(',').map((s) => s.trim()).filter(Boolean));
      }
    }
  }, [user, isOpen]);

  if (!isOpen || !user) return null;

  const toggleSubject = (subject: string) => {
    setSelectedSubjects((prev) =>
      prev.includes(subject) ? prev.filter((s) => s !== subject) : [...prev, subject]
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      // 1. Update Profile (Name & Grade)
      const updatedUser = await api.updateProfile({
        full_name: fullName.trim(),
        grade_level: gradeLevel,
      });

      // 2. Update Student Preferences
      const prefPayload: StudentPreferences = {
        preferred_explanation_level: explanationLevel,
        preferred_voice: preferredVoice,
        preferred_playback_speed: playbackSpeed,
        preferred_language: language,
        preferred_subjects: selectedSubjects,
      };
      await api.updatePreferences(prefPayload);

      // 3. Notify parent with combined state
      const mergedUser: User = {
        ...updatedUser,
        preferred_explanation_level: explanationLevel,
        preferred_voice: preferredVoice,
        preferred_playback_speed: playbackSpeed,
        preferred_language: language,
        preferred_subjects: selectedSubjects.join(','),
      };

      onProfileUpdated(mergedUser);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2500);
    } catch (err: any) {
      setError(err.message || 'Failed to update preferences.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-6 sm:p-8 w-full max-w-lg shadow-2xl border border-slate-100 relative animate-in fade-in zoom-in-95 duration-150 max-h-[92vh] flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* User Summary Header */}
        <div className="flex items-center gap-4 mb-4">
          <div className="w-13 h-13 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white flex items-center justify-center text-xl font-bold shadow-lg shadow-sky-100 p-3">
            {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'S'}
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">{user.full_name}</h3>
            <p className="text-xs text-slate-500">{user.email}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-100 text-sky-800">
                {user.grade_level}
              </span>
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 capitalize">
                {explanationLevel} Mode
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-100 mb-4 gap-4 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('profile')}
            className={`pb-2.5 transition-colors border-b-2 ${
              activeTab === 'profile'
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-400 hover:text-slate-700'
            }`}
          >
            Academic Profile
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('preferences')}
            className={`pb-2.5 transition-colors border-b-2 flex items-center gap-1.5 ${
              activeTab === 'preferences'
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-400 hover:text-slate-700'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Learning & Voice Preferences
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2">
            <Check className="w-4 h-4 shrink-0" />
            <span>Profile and learning preferences successfully updated!</span>
          </div>
        )}

        <form onSubmit={handleSave} className="flex-1 overflow-y-auto pr-1 space-y-4">
          {activeTab === 'profile' ? (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="w-full text-sm pl-10 pr-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Academic Grade Level</label>
                <div className="relative">
                  <GraduationCap className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <select
                    value={gradeLevel}
                    onChange={(e) => setGradeLevel(e.target.value)}
                    className="w-full text-sm pl-10 pr-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
                  >
                    <option value="Middle School (Grades 6-8)">Middle School (Grades 6-8)</option>
                    <option value="Grade 9">Grade 9 (Secondary Foundation)</option>
                    <option value="Grade 10">Grade 10 (Secondary Board)</option>
                    <option value="Grade 11 STEM">Grade 11 STEM (Physics, Chemistry, Math)</option>
                    <option value="Grade 12 STEM">Grade 12 STEM (Advanced Board & Exam Prep)</option>
                    <option value="Undergraduate">College / University Undergraduate</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 text-xs text-slate-400 flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5" />
                <span>Member since: {new Date(user.created_at).toLocaleDateString()}</span>
              </div>
            </>
          ) : (
            <>
              {/* Explanation Level */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-sky-600" />
                  Explanation Rigor Level
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                    <button
                      key={level}
                      type="button"
                      onClick={() => setExplanationLevel(level)}
                      className={`p-2.5 rounded-xl border text-xs font-semibold capitalize text-center transition-all ${
                        explanationLevel === level
                          ? 'border-sky-600 bg-sky-50 text-sky-800 shadow-sm'
                          : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                      }`}
                    >
                      {level}
                      <span className="block text-[10px] font-normal text-slate-400 mt-0.5">
                        {level === 'beginner'
                          ? 'Intuitive'
                          : level === 'intermediate'
                          ? 'Standard'
                          : 'Rigorous'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Preferred AI Voice */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Volume2 className="w-3.5 h-3.5 text-sky-600" />
                  Preferred Neural Voice
                </label>
                <select
                  value={preferredVoice}
                  onChange={(e) => setPreferredVoice(e.target.value)}
                  className="w-full text-xs border border-slate-200 rounded-xl px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  {AVAILABLE_VOICES.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Playback Speed */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Gauge className="w-3.5 h-3.5 text-sky-600" />
                  Default Speech Playback Speed
                </label>
                <div className="flex gap-2">
                  {SPEED_OPTIONS.map((spd) => (
                    <button
                      key={spd}
                      type="button"
                      onClick={() => setPlaybackSpeed(spd)}
                      className={`flex-1 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                        playbackSpeed === spd
                          ? 'border-sky-600 bg-sky-600 text-white'
                          : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      {spd}x
                    </button>
                  ))}
                </div>
              </div>

              {/* Language */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Languages className="w-3.5 h-3.5 text-sky-600" />
                  Preferred Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full text-xs border border-slate-200 rounded-xl px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  {LANGUAGE_OPTIONS.map((lang) => (
                    <option key={lang.id} value={lang.id}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Preferred Academic Subjects */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-sky-600" />
                  Primary Subjects of Interest
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {SUBJECT_OPTIONS.map((sub) => {
                    const isSelected = selectedSubjects.includes(sub);
                    return (
                      <button
                        key={sub}
                        type="button"
                        onClick={() => toggleSubject(sub)}
                        className={`text-xs px-2.5 py-1 rounded-lg border font-medium transition-all ${
                          isSelected
                            ? 'bg-sky-50 border-sky-300 text-sky-700 font-semibold'
                            : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {isSelected ? '✓ ' : '+ '}
                        {sub}
                      </button>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-slate-100 mt-4">
            <button
              type="button"
              onClick={onLogout}
              className="px-3 py-2 text-rose-600 hover:bg-rose-50 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Close
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-5 py-2 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-200 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
              >
                {saving ? (
                  'Saving...'
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
