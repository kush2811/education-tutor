import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  X,
  Gauge,
  Loader2,
  AlertCircle,
  FileText,
  SkipForward,
  SkipBack,
} from 'lucide-react';
import { api } from '../services/api';
import { TTSVoiceResponse, SentenceSegment } from '../types';

interface VoicePlayerProps {
  textToSpeak: string;
  onClose: () => void;
}

const AVAILABLE_VOICES = [
  { id: 'en-US-AriaNeural', name: 'Aria (Warm Female)' },
  { id: 'en-US-GuyNeural', name: 'Guy (Natural Male)' },
  { id: 'en-US-JennyNeural', name: 'Jenny (Expressive Female)' },
  { id: 'en-US-ChristopherNeural', name: 'Christopher (Academic Male)' },
];

const SPEED_OPTIONS = [0.75, 1.0, 1.25, 1.5, 2.0];

export const VoicePlayer: React.FC<VoicePlayerProps> = ({ textToSpeak, onClose }) => {
  // Voice Generation & Audio State
  const [loading, setLoading] = useState(true);
  const [voiceData, setVoiceData] = useState<TTSVoiceResponse | null>(null);
  const [selectedVoice, setSelectedVoice] = useState('en-US-AriaNeural');
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(0);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [currentWordIndex, setCurrentWordIndex] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isTextOnlyMode, setIsTextOnlyMode] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const activeSubtitleRef = useRef<HTMLDivElement | null>(null);
  const browserUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const progressTimerRef = useRef<number | null>(null);

  // 1. Fetch Audio & Synchronized Timestamps from Backend
  const loadSpeechData = async (voiceId: string) => {
    setLoading(true);
    setErrorMessage(null);
    setIsPlaying(false);
    setCurrentTime(0);
    setCurrentSentenceIndex(0);
    setCurrentWordIndex(null);

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    try {
      const res = await api.generateVoice({
        text: textToSpeak,
        voice: voiceId,
        rate: '+0%',
      });

      setVoiceData(res);
      setTotalDuration(res.duration_seconds || 10);

      // If backend generated neural audio file
      if (res.audio_url && res.audio_format === 'mp3') {
        const fullAudioUrl = res.audio_url.startsWith('http')
          ? res.audio_url
          : `http://127.0.0.1:8000${res.audio_url}`;

        const audio = new Audio(fullAudioUrl);
        audio.playbackRate = playbackSpeed;
        audioRef.current = audio;

        audio.onloadedmetadata = () => {
          if (audio.duration && !isNaN(audio.duration) && audio.duration !== Infinity) {
            setTotalDuration(audio.duration);
          }
        };

        audio.ontimeupdate = () => {
          handleAudioTimeUpdate(audio.currentTime, res.sentence_segments);
        };

        audio.onended = () => {
          setIsPlaying(false);
          setCurrentTime(totalDuration);
          setCurrentWordIndex(null);
        };

        audio.onerror = () => {
          console.warn('Audio streaming failed, switching to client-side speech fallback.');
          setErrorMessage('Streaming audio encountered network interruption; switched to client voice.');
        };
      }
    } catch (err: any) {
      console.warn('Backend TTS call failed:', err);
      setErrorMessage(err.message || 'Voice service offline; using client speech synthesis.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSpeechData(selectedVoice);

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
      }
    };
  }, [textToSpeak, selectedVoice]);

  // 2. Synchronize active sentence and word timestamps
  const handleAudioTimeUpdate = (time: number, segments: SentenceSegment[]) => {
    setCurrentTime(time);

    // Find matching sentence
    const sIdx = segments.findIndex(
      (s) => time >= s.start_time && time <= s.end_time
    );

    if (sIdx !== -1) {
      setCurrentSentenceIndex(sIdx);

      // Find matching word if word segments are available
      const currentSentence = segments[sIdx];
      if (currentSentence && currentSentence.words && currentSentence.words.length > 0) {
        const wIdx = currentSentence.words.findIndex(
          (w) => time >= w.start_time && time <= w.end_time
        );
        setCurrentWordIndex(wIdx !== -1 ? wIdx : null);
      } else {
        setCurrentWordIndex(null);
      }
    } else if (segments.length > 0 && time > segments[segments.length - 1].end_time) {
      setCurrentSentenceIndex(segments.length - 1);
      setCurrentWordIndex(null);
    }

    // Auto-scroll the active subtitle into view
    if (activeSubtitleRef.current) {
      activeSubtitleRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  };

  // 3. Browser Speech Synthesis Fallback Handler
  const playWithBrowserSpeech = (startFromIdx = 0) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const segments = voiceData?.sentence_segments || [];
    const textChunk = segments
      .slice(startFromIdx)
      .map((s) => s.spoken_text || s.display_text)
      .join(' ');

    const utterance = new SpeechSynthesisUtterance(textChunk || textToSpeak);
    utterance.rate = playbackSpeed;
    browserUtteranceRef.current = utterance;

    utterance.onend = () => {
      setIsPlaying(false);
      setCurrentTime(totalDuration);
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    };

    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);

    // Proportional progress timer for fallback mode
    const intervalMs = 250;
    if (progressTimerRef.current) clearInterval(progressTimerRef.current);

    progressTimerRef.current = window.setInterval(() => {
      setCurrentTime((prev) => {
        const next = prev + (intervalMs / 1000) * playbackSpeed;
        if (segments.length > 0) {
          handleAudioTimeUpdate(next, segments);
        }
        if (next >= totalDuration) {
          if (progressTimerRef.current) clearInterval(progressTimerRef.current);
          setIsPlaying(false);
          return totalDuration;
        }
        return next;
      });
    }, intervalMs);
  };

  // 4. Playback Controls
  const togglePlayPause = () => {
    if (isTextOnlyMode) {
      setIsTextOnlyMode(false);
    }

    if (isPlaying) {
      // Pause
      if (audioRef.current && audioRef.current.src) {
        audioRef.current.pause();
      } else if ('speechSynthesis' in window) {
        window.speechSynthesis.pause();
      }
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
      setIsPlaying(false);
    } else {
      // Resume / Play
      if (audioRef.current && audioRef.current.src) {
        audioRef.current
          .play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.warn('Audio play failed, falling back to browser speech:', err);
            playWithBrowserSpeech(currentSentenceIndex);
          });
      } else {
        if ('speechSynthesis' in window && window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
          setIsPlaying(true);
        } else {
          playWithBrowserSpeech(currentSentenceIndex);
        }
      }
    }
  };

  const handleReplay = () => {
    setCurrentTime(0);
    setCurrentSentenceIndex(0);
    setCurrentWordIndex(null);

    if (audioRef.current && audioRef.current.src) {
      audioRef.current.currentTime = 0;
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => playWithBrowserSpeech(0));
    } else {
      playWithBrowserSpeech(0);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const targetTime = Number(e.target.value);
    setCurrentTime(targetTime);

    const segments = voiceData?.sentence_segments || [];
    handleAudioTimeUpdate(targetTime, segments);

    if (audioRef.current && audioRef.current.src) {
      audioRef.current.currentTime = targetTime;
    } else if (isPlaying) {
      // Re-trigger browser speech from matching sentence
      const targetIdx = segments.findIndex((s) => targetTime >= s.start_time && targetTime <= s.end_time);
      playWithBrowserSpeech(targetIdx !== -1 ? targetIdx : 0);
    }
  };

  const handleSentenceClick = (idx: number) => {
    const segments = voiceData?.sentence_segments || [];
    if (!segments[idx]) return;

    const targetTime = segments[idx].start_time;
    setCurrentTime(targetTime);
    setCurrentSentenceIndex(idx);
    setCurrentWordIndex(null);

    if (audioRef.current && audioRef.current.src) {
      audioRef.current.currentTime = targetTime;
      if (!isPlaying) {
        audioRef.current.play().then(() => setIsPlaying(true));
      }
    } else {
      playWithBrowserSpeech(idx);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
    if (isPlaying && (!audioRef.current || !audioRef.current.src)) {
      playWithBrowserSpeech(currentSentenceIndex);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const segments = voiceData?.sentence_segments || [];

  return (
    <div className="bg-slate-900 text-white border-t border-slate-800 p-4 shadow-2xl relative animate-in slide-in-from-bottom-3 duration-200">
      <div className="max-w-4xl mx-auto flex flex-col gap-3">
        {/* Header Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center">
              <Volume2 className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-sky-400 uppercase tracking-wider block">
                Conversational Voice Tutor
              </span>
              <span className="text-[10px] text-slate-400">
                {voiceData?.alignment_method === 'neural_speech_timestamps'
                  ? 'Neural Edge-TTS with Aligned Subtitles'
                  : 'Client-Synchronized Audio Subtitles'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Text-Only Mode Toggle */}
            <button
              onClick={() => {
                if (isPlaying) togglePlayPause();
                setIsTextOnlyMode(!isTextOnlyMode);
              }}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                isTextOnlyMode
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-slate-800 text-slate-300 hover:text-white border border-slate-700'
              }`}
              title="Toggle reading mode without audio"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{isTextOnlyMode ? 'Exit Text-Only' : 'Text-Only Mode'}</span>
            </button>

            {/* Voice Selector */}
            <select
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              className="bg-slate-800 text-slate-200 text-xs rounded-lg px-2 py-1 border border-slate-700 outline-none focus:border-sky-500"
              title="Select AI Tutor Voice"
            >
              {AVAILABLE_VOICES.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>

            {/* Close Button */}
            <button
              onClick={() => {
                if (audioRef.current) audioRef.current.pause();
                if ('speechSynthesis' in window) window.speechSynthesis.cancel();
                onClose();
              }}
              className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              title="Close voice interface"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Error / Fallback Banner if any */}
        {errorMessage && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl px-3 py-1.5 flex items-center gap-2 text-xs text-amber-300">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="bg-slate-800/80 rounded-2xl p-6 border border-slate-700/80 flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 text-sky-400 animate-spin" />
            <span className="text-xs text-slate-300 font-medium">
              Generating natural voice audio and calculating synchronized word timestamps...
            </span>
          </div>
        ) : isTextOnlyMode ? (
          /* Text-Only Reading Mode Display */
          <div className="bg-slate-800/80 rounded-2xl p-4 border border-slate-700/80 max-h-48 overflow-y-auto">
            <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-700/60">
              <span className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-sky-400" />
                Text-Only Mode (Read at your own pace)
              </span>
              <button
                onClick={() => setIsTextOnlyMode(false)}
                className="text-[10px] text-sky-400 hover:underline"
              >
                Resume Voice Audio
              </button>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{textToSpeak}</p>
          </div>
        ) : (
          /* Active Subtitle Highlighting Card */
          <div className="bg-slate-800/90 rounded-2xl p-4 border border-slate-700/80 max-h-36 overflow-y-auto shadow-inner">
            <div className="flex flex-col gap-2">
              {segments.length > 0 ? (
                segments.map((seg, idx) => {
                  const isCurrent = idx === currentSentenceIndex;
                  return (
                    <div
                      key={idx}
                      ref={isCurrent ? activeSubtitleRef : null}
                      onClick={() => handleSentenceClick(idx)}
                      className={`text-xs leading-relaxed transition-all rounded-xl p-2 cursor-pointer ${
                        isCurrent
                          ? 'bg-sky-500/20 text-white font-medium border-l-4 border-sky-400 shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-750'
                      }`}
                    >
                      {isCurrent && seg.words && seg.words.length > 0 ? (
                        /* Word-Level Highlighting within active sentence */
                        <span>
                          {seg.words.map((w, wIdx) => {
                            const isCurrentWord = wIdx === currentWordIndex;
                            return (
                              <span
                                key={wIdx}
                                className={`transition-all rounded px-0.5 ${
                                  isCurrentWord
                                    ? 'bg-amber-400 text-slate-950 font-bold shadow-xs'
                                    : ''
                                }`}
                              >
                                {w.word}{' '}
                              </span>
                            );
                          })}
                        </span>
                      ) : (
                        <span>{seg.display_text}</span>
                      )}
                    </div>
                  );
                })
              ) : (
                <p className="text-xs text-slate-400 italic">No subtitle segments available.</p>
              )}
            </div>
          </div>
        )}

        {/* Audio Controls & Timeline Scrubber */}
        {!isTextOnlyMode && (
          <div className="flex flex-col gap-2 bg-slate-800/50 rounded-2xl p-3 border border-slate-700/50">
            {/* Timeline slider */}
            <div className="flex items-center gap-3">
              <span className="text-[11px] font-mono text-slate-400 w-10 text-right">
                {formatTime(currentTime)}
              </span>

              <input
                type="range"
                min={0}
                max={totalDuration || 10}
                step={0.1}
                value={currentTime}
                onChange={handleSeek}
                className="flex-1 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-400"
                title="Seek audio position"
              />

              <span className="text-[11px] font-mono text-slate-400 w-10">
                {formatTime(totalDuration)}
              </span>
            </div>

            {/* Playback Controls & Speed */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                {/* Previous Sentence */}
                <button
                  onClick={() => {
                    if (currentSentenceIndex > 0) {
                      handleSentenceClick(currentSentenceIndex - 1);
                    }
                  }}
                  disabled={currentSentenceIndex <= 0}
                  className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 rounded-lg hover:bg-slate-700 transition-colors"
                  title="Previous sentence"
                >
                  <SkipBack className="w-4 h-4" />
                </button>

                {/* Play/Pause Button */}
                <button
                  onClick={togglePlayPause}
                  className="p-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold transition-all shadow-md shadow-sky-500/20 active:scale-95"
                  title={isPlaying ? 'Pause audio' : 'Play audio'}
                >
                  {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
                </button>

                {/* Next Sentence */}
                <button
                  onClick={() => {
                    if (currentSentenceIndex < segments.length - 1) {
                      handleSentenceClick(currentSentenceIndex + 1);
                    }
                  }}
                  disabled={currentSentenceIndex >= segments.length - 1}
                  className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 rounded-lg hover:bg-slate-700 transition-colors"
                  title="Next sentence"
                >
                  <SkipForward className="w-4 h-4" />
                </button>

                {/* Replay */}
                <button
                  onClick={handleReplay}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-700 transition-colors"
                  title="Replay from start"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>

              {/* Speed Controls */}
              <div className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-700/50">
                <Gauge className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
                {SPEED_OPTIONS.map((speed) => (
                  <button
                    key={speed}
                    onClick={() => handleSpeedChange(speed)}
                    className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold transition-all ${
                      playbackSpeed === speed
                        ? 'bg-sky-500 text-slate-950'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
