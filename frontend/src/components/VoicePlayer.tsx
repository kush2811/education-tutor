import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  X,
  Gauge,
} from 'lucide-react';

interface VoicePlayerProps {
  textToSpeak: string;
  onClose: () => void;
}

export const VoicePlayer: React.FC<VoicePlayerProps> = ({ textToSpeak, onClose }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [currentProgress, setCurrentProgress] = useState(0); // 0 to 100
  const [currentTimeSec, setCurrentTimeSec] = useState(0);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);

  // Split text into readable sentences for subtitle highlighting
  const sentences = React.useMemo(() => {
    const raw = textToSpeak.match(/[^.!?]+[.!?]+(\s|$)|[^.!?]+$/g) || [textToSpeak];
    return raw.map((s) => s.trim()).filter(Boolean);
  }, [textToSpeak]);

  const estimatedDurationSec = Math.max(5, Math.ceil(textToSpeak.split(' ').length / 2.5));
  const progressTimerRef = useRef<number | null>(null);

  // Browser SpeechSynthesis fallback for real audio voice generation in Phase 2
  const speakWithBrowserSpeech = (startFromSentence = 0) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(sentences.slice(startFromSentence).join(' '));
    utterance.rate = playbackSpeed;

    utterance.onboundary = (e) => {
      if (e.name === 'sentence') {
        const charIdx = e.charIndex;
        let cumulative = 0;
        for (let i = 0; i < sentences.length; i++) {
          cumulative += sentences[i].length + 1;
          if (charIdx < cumulative) {
            setCurrentSentenceIndex(i);
            break;
          }
        }
      }
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setCurrentProgress(100);
      setCurrentTimeSec(estimatedDurationSec);
    };

    window.speechSynthesis.speak(utterance);
  };

  const handleTogglePlay = () => {
    if (isPlaying) {
      if ('speechSynthesis' in window) window.speechSynthesis.pause();
      setIsPlaying(false);
    } else {
      if ('speechSynthesis' in window && window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      } else {
        speakWithBrowserSpeech(currentSentenceIndex);
      }
      setIsPlaying(true);
    }
  };

  const handleReplay = () => {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    setCurrentProgress(0);
    setCurrentTimeSec(0);
    setCurrentSentenceIndex(0);
    speakWithBrowserSpeech(0);
    setIsPlaying(true);
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (isPlaying) {
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      speakWithBrowserSpeech(currentSentenceIndex);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setCurrentProgress(val);
    const targetSec = Math.floor((val / 100) * estimatedDurationSec);
    setCurrentTimeSec(targetSec);
    const targetIdx = Math.min(
      sentences.length - 1,
      Math.floor((val / 100) * sentences.length)
    );
    setCurrentSentenceIndex(targetIdx);
    if (isPlaying) {
      speakWithBrowserSpeech(targetIdx);
    }
  };

  useEffect(() => {
    if (isPlaying) {
      progressTimerRef.current = window.setInterval(() => {
        setCurrentTimeSec((prev) => {
          const next = prev + 0.5 * playbackSpeed;
          const prog = Math.min(100, (next / estimatedDurationSec) * 100);
          setCurrentProgress(prog);
          const sIdx = Math.min(
            sentences.length - 1,
            Math.floor((prog / 100) * sentences.length)
          );
          setCurrentSentenceIndex(sIdx);
          if (next >= estimatedDurationSec) {
            setIsPlaying(false);
            return estimatedDurationSec;
          }
          return next;
        });
      }, 500);
    } else {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    }

    return () => {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    };
  }, [isPlaying, playbackSpeed, estimatedDurationSec, sentences.length]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="bg-slate-900 text-white border-t border-slate-800 p-4 shadow-2xl relative animate-in slide-in-from-bottom-3 duration-200">
      <div className="max-w-4xl mx-auto flex flex-col gap-3">
        {/* Header & Status Indicator */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center">
              <Volume2 className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-bold text-sky-400 uppercase tracking-wider">
              Conversational Audio Tutor
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium">
              Preview Mode (Web Speech & Sentence Highlighter; Neural Edge-TTS connects in Phase 6)
            </span>
          </div>

          <button
            onClick={() => {
              if ('speechSynthesis' in window) window.speechSynthesis.cancel();
              onClose();
            }}
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            title="Close voice interface"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Subtitle Display Area with Active Sentence Highlighting */}
        <div className="bg-slate-800/80 rounded-2xl p-3 border border-slate-700/80 min-h-[64px] max-h-24 overflow-y-auto">
          <p className="text-xs leading-relaxed text-slate-400">
            {sentences.map((sentence, idx) => {
              const isActive = idx === currentSentenceIndex;
              return (
                <span
                  key={idx}
                  className={`transition-all rounded px-1 py-0.5 ${
                    isActive
                      ? 'bg-sky-500/30 text-white font-semibold border-b-2 border-sky-400'
                      : 'hover:text-slate-200 cursor-pointer'
                  }`}
                  onClick={() => {
                    setCurrentSentenceIndex(idx);
                    setCurrentProgress((idx / sentences.length) * 100);
                    speakWithBrowserSpeech(idx);
                    setIsPlaying(true);
                  }}
                >
                  {sentence}{' '}
                </span>
              );
            })}
          </p>
        </div>

        {/* Audio Controls & Timeline */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={handleReplay}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
              title="Replay from start"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <button
              onClick={handleTogglePlay}
              className="w-10 h-10 rounded-xl bg-sky-600 hover:bg-sky-500 text-white flex items-center justify-center shadow-lg shadow-sky-600/30 transition-transform active:scale-95"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
            </button>
          </div>

          {/* Progress Bar & Time */}
          <div className="flex-1 flex items-center gap-3">
            <span className="text-[11px] font-mono text-slate-400 w-9 text-right">
              {formatTime(currentTimeSec)}
            </span>
            <input
              type="range"
              min="0"
              max="100"
              value={currentProgress}
              onChange={handleSeek}
              className="flex-1 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-500"
            />
            <span className="text-[11px] font-mono text-slate-400 w-9">
              {formatTime(estimatedDurationSec)}
            </span>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1 shrink-0 bg-slate-800 p-1 rounded-xl border border-slate-700">
            <Gauge className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            {[0.75, 1.0, 1.25, 1.5].map((s) => (
              <button
                key={s}
                onClick={() => handleSpeedChange(s)}
                className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition-colors ${
                  playbackSpeed === s
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
