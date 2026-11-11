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
import { api, API_ORIGIN } from '../services/api';
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
  const rafRef = useRef<number | null>(null);
  const speechSessionRef = useRef<number>(0);
  const voiceDataRef = useRef<TTSVoiceResponse | null>(null);

  useEffect(() => {
    voiceDataRef.current = voiceData;
  }, [voiceData]);

  // Smooth auto-scroll ONLY when moving to a new line
  useEffect(() => {
    if (activeSubtitleRef.current) {
      activeSubtitleRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [currentSentenceIndex]);

  const stopAllPlayback = () => {
    speechSessionRef.current += 1;
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
  };

  // Fetch Audio & Synchronized Word Timestamps from Backend
  const loadSpeechData = async (voiceId: string) => {
    stopAllPlayback();
    setLoading(true);
    setErrorMessage(null);
    setCurrentTime(0);
    setCurrentSentenceIndex(0);
    setCurrentWordIndex(null);

    if (audioRef.current) {
      audioRef.current.src = '';
      audioRef.current = null;
    }

    try {
      const res = await api.generateVoice({
        text: textToSpeak,
        voice: voiceId,
        rate: '+0%',
      });

      setVoiceData(res);
      voiceDataRef.current = res;
      setTotalDuration(res.duration_seconds || 10);

      if (res.audio_url && res.audio_format === 'mp3') {
        const fullAudioUrl = res.audio_url.startsWith('http')
          ? res.audio_url
          : `${API_ORIGIN}${res.audio_url}`;

        const audio = new Audio(fullAudioUrl);
        audio.playbackRate = playbackSpeed;
        audioRef.current = audio;

        audio.onloadedmetadata = () => {
          if (audio.duration && !isNaN(audio.duration) && audio.duration !== Infinity) {
            setTotalDuration(audio.duration);
          }
        };

        audio.onended = () => {
          if (rafRef.current) cancelAnimationFrame(rafRef.current);
          setIsPlaying(false);
          setCurrentTime(audio.duration || res.duration_seconds || 0);
          setCurrentWordIndex(null);
        };

        audio.onerror = () => {
          audioRef.current = null;
          setErrorMessage('Audio file unavailable; using browser speech line-by-line.');
        };
      }
    } catch (err: any) {
      console.warn('Backend TTS call failed:', err);
      setErrorMessage(err.message || 'Voice service offline; using browser speech synthesis.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSpeechData(selectedVoice);
    return () => {
      stopAllPlayback();
      if (audioRef.current) {
        audioRef.current.src = '';
      }
    };
  }, [textToSpeak, selectedVoice]);

  // Gap-tolerant sentence and word lookup for neural MP3 playback
  const syncTimestampsFromAudioTime = (time: number, segments: SentenceSegment[]) => {
    setCurrentTime(time);
    if (!segments || segments.length === 0) return;

    // Select the active sentence whose start_time <= time (tolerant of inter-sentence pauses)
    let sIdx = 0;
    for (let i = 0; i < segments.length; i++) {
      if (time + 0.04 >= segments[i].start_time) {
        sIdx = i;
      } else {
        break;
      }
    }
    setCurrentSentenceIndex(sIdx);

    const seg = segments[sIdx];
    if (seg && seg.words && seg.words.length > 0) {
      // If before the first word or past the sentence end, highlight closest boundary appropriately
      let matchedWordIdx: number | null = null;
      for (let j = 0; j < seg.words.length; j++) {
        const w = seg.words[j];
        if (time >= w.start_time - 0.03 && time <= w.end_time + 0.04) {
          matchedWordIdx = j;
          break;
        }
        if (time >= w.start_time) {
          matchedWordIdx = j;
        }
      }
      if (time > seg.end_time + 0.15) {
        matchedWordIdx = null;
      }
      setCurrentWordIndex(matchedWordIdx);
    } else {
      setCurrentWordIndex(null);
    }
  };

  // High-precision 60fps synchronization loop while MP3 is playing
  useEffect(() => {
    if (!isPlaying || !audioRef.current) {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      return;
    }

    const tick = () => {
      const audio = audioRef.current;
      const segs = voiceDataRef.current?.sentence_segments || [];
      if (audio && !audio.paused) {
        syncTimestampsFromAudioTime(audio.currentTime, segs);
        rafRef.current = requestAnimationFrame(tick);
      }
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [isPlaying]);

  // Line-by-line Browser Speech Fallback with true utterance.onboundary tracking
  const speakLineByLine = (startIdx: number, speedOverride?: number) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const segments = voiceDataRef.current?.sentence_segments || [];
    const activeSpeed = speedOverride ?? playbackSpeed;
    const sessionToken = ++speechSessionRef.current;

    if (segments.length === 0) {
      const utt = new SpeechSynthesisUtterance(textToSpeak);
      utt.rate = activeSpeed;
      utt.onend = () => {
        if (speechSessionRef.current === sessionToken) setIsPlaying(false);
      };
      setIsPlaying(true);
      window.speechSynthesis.speak(utt);
      return;
    }

    const speakNext = (idx: number) => {
      if (speechSessionRef.current !== sessionToken) return;
      if (idx >= segments.length) {
        setIsPlaying(false);
        setCurrentWordIndex(null);
        setCurrentTime(totalDuration);
        return;
      }

      const seg = segments[idx];
      const spokenLine = seg.spoken_text || seg.display_text;
      const utt = new SpeechSynthesisUtterance(spokenLine);
      utt.rate = activeSpeed;

      // Precompute character offsets of each word in spokenLine for accurate boundary tracking
      const wordOffsets: { start: number; end: number }[] = [];
      let searchFrom = 0;
      const splitWords = spokenLine.split(/\s+/).filter(Boolean);
      for (const w of splitWords) {
        const pos = spokenLine.indexOf(w, searchFrom);
        if (pos !== -1) {
          wordOffsets.push({ start: pos, end: pos + w.length });
          searchFrom = pos + w.length;
        }
      }

      utt.onstart = () => {
        if (speechSessionRef.current !== sessionToken) return;
        setCurrentSentenceIndex(idx);
        setCurrentWordIndex(0);
        setCurrentTime(seg.start_time);
      };

      utt.onboundary = (event: SpeechSynthesisEvent) => {
        if (speechSessionRef.current !== sessionToken) return;
        if (event.name === 'word' || typeof event.charIndex === 'number') {
          const ch = event.charIndex;
          const wIdx = wordOffsets.findIndex((o) => ch >= o.start && ch <= o.end);
          if (wIdx !== -1) {
            setCurrentWordIndex(wIdx);
            if (seg.words && seg.words[wIdx]) {
              setCurrentTime(seg.words[wIdx].start_time);
            }
          }
        }
      };

      utt.onend = () => {
        if (speechSessionRef.current !== sessionToken) return;
        setCurrentTime(seg.end_time);
        speakNext(idx + 1);
      };

      utt.onerror = () => {
        if (speechSessionRef.current === sessionToken) {
          setIsPlaying(false);
        }
      };

      window.speechSynthesis.speak(utt);
    };

    setIsPlaying(true);
    speakNext(Math.max(0, Math.min(startIdx, segments.length - 1)));
  };

  // Playback Controls
  const togglePlayPause = () => {
    if (isTextOnlyMode) {
      setIsTextOnlyMode(false);
    }

    if (isPlaying) {
      stopAllPlayback();
      return;
    }

    if (audioRef.current && audioRef.current.src) {
      audioRef.current.playbackRate = playbackSpeed;
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => {
          audioRef.current = null;
          speakLineByLine(currentSentenceIndex);
        });
    } else {
      speakLineByLine(currentSentenceIndex);
    }
  };

  const handleReplay = () => {
    stopAllPlayback();
    setCurrentTime(0);
    setCurrentSentenceIndex(0);
    setCurrentWordIndex(null);

    if (audioRef.current && audioRef.current.src) {
      audioRef.current.currentTime = 0;
      audioRef.current.playbackRate = playbackSpeed;
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => speakLineByLine(0));
    } else {
      speakLineByLine(0);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const targetTime = Number(e.target.value);
    const segments = voiceData?.sentence_segments || [];
    syncTimestampsFromAudioTime(targetTime, segments);

    if (audioRef.current && audioRef.current.src) {
      audioRef.current.currentTime = targetTime;
    } else if (isPlaying) {
      let targetIdx = 0;
      for (let i = 0; i < segments.length; i++) {
        if (targetTime >= segments[i].start_time) targetIdx = i;
      }
      speakLineByLine(targetIdx);
    }
  };

  const handleSentenceClick = (idx: number) => {
    const segments = voiceData?.sentence_segments || [];
    if (!segments[idx]) return;

    const targetTime = segments[idx].start_time;
    setCurrentTime(targetTime);
    setCurrentSentenceIndex(idx);
    setCurrentWordIndex(0);

    if (audioRef.current && audioRef.current.src) {
      audioRef.current.currentTime = targetTime;
      audioRef.current.playbackRate = playbackSpeed;
      if (!isPlaying) {
        audioRef.current
          .play()
          .then(() => setIsPlaying(true))
          .catch(() => speakLineByLine(idx));
      }
    } else {
      speakLineByLine(idx);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (audioRef.current && audioRef.current.src) {
      audioRef.current.playbackRate = speed;
    } else if (isPlaying) {
      speakLineByLine(currentSentenceIndex, speed);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const segments = voiceData?.sentence_segments || [];

  return (
    <div className="bg-slate-900 text-white border-t border-slate-800 p-4 shadow-2xl relative z-20">
      <div className="max-w-4xl mx-auto flex flex-col gap-3">
        {/* Header Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center">
              <Volume2 className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-sky-400 uppercase tracking-wider block">
                Voice Reader
              </span>
              <span className="text-[10px] text-slate-400">
                {voiceData?.alignment_method === 'neural_speech_timestamps'
                  ? 'Neural Voice with Word-by-Word Subtitles'
                  : 'Line-by-Line Synchronized Speech'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (isPlaying) stopAllPlayback();
                setIsTextOnlyMode(!isTextOnlyMode);
              }}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                isTextOnlyMode
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-slate-800 text-slate-300 hover:text-white border border-slate-700'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{isTextOnlyMode ? 'Exit Text-Only' : 'Text-Only'}</span>
            </button>

            <select
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              className="bg-slate-800 text-slate-200 text-xs rounded-lg px-2 py-1 border border-slate-700 outline-none focus:border-sky-500"
              title="Select Voice"
            >
              {AVAILABLE_VOICES.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>

            <button
              onClick={() => {
                stopAllPlayback();
                onClose();
              }}
              className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              title="Close voice reader"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl px-3 py-1.5 flex items-center gap-2 text-xs text-amber-300">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {loading ? (
          <div className="bg-slate-800/80 rounded-2xl p-6 border border-slate-700/80 flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 text-sky-400 animate-spin" />
            <span className="text-xs text-slate-300 font-medium">
              Preparing audio and aligning line-by-line timestamps...
            </span>
          </div>
        ) : isTextOnlyMode ? (
          <div className="bg-slate-800/80 rounded-2xl p-4 border border-slate-700/80 max-h-48 overflow-y-auto">
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{textToSpeak}</p>
          </div>
        ) : (
          /* Synchronized Line-by-Line Subtitle Card */
          <div className="bg-slate-800/90 rounded-2xl p-4 border border-slate-700/80 max-h-40 overflow-y-auto shadow-inner">
            <div className="flex flex-col gap-2">
              {segments.length > 0 ? (
                segments.map((seg, idx) => {
                  const isCurrent = idx === currentSentenceIndex;
                  const displayWords =
                    seg.words && seg.words.length > 0
                      ? seg.words.map((w) => w.word)
                      : (seg.spoken_text || seg.display_text).split(/\s+/).filter(Boolean);

                  return (
                    <div
                      key={idx}
                      ref={isCurrent ? activeSubtitleRef : null}
                      onClick={() => handleSentenceClick(idx)}
                      className={`text-xs leading-relaxed transition-colors rounded-xl p-2 cursor-pointer ${
                        isCurrent
                          ? 'bg-sky-500/20 text-white font-medium border-l-4 border-sky-400'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {isCurrent && displayWords.length > 0 ? (
                        <span>
                          {displayWords.map((wordText, wIdx) => (
                            <span
                              key={wIdx}
                              className={`rounded px-0.5 transition-colors ${
                                wIdx === currentWordIndex
                                  ? 'bg-amber-400 text-slate-950 font-bold'
                                  : ''
                              }`}
                            >
                              {wordText}{' '}
                            </span>
                          ))}
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

        {/* Audio Scrubber & Playback Controls */}
        {!isTextOnlyMode && !loading && (
          <div className="flex flex-col gap-2 bg-slate-800/50 rounded-2xl p-3 border border-slate-700/50">
            <div className="flex items-center gap-3">
              <span className="text-[11px] font-mono text-slate-400 w-10 text-right">
                {formatTime(currentTime)}
              </span>

              <input
                type="range"
                min={0}
                max={totalDuration || 10}
                step={0.1}
                value={Math.min(currentTime, totalDuration || 10)}
                onChange={handleSeek}
                className="flex-1 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-400"
                title="Seek position"
              />

              <span className="text-[11px] font-mono text-slate-400 w-10">
                {formatTime(totalDuration)}
              </span>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => currentSentenceIndex > 0 && handleSentenceClick(currentSentenceIndex - 1)}
                  disabled={currentSentenceIndex <= 0}
                  className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 rounded-lg hover:bg-slate-700 transition-colors"
                  title="Previous line"
                >
                  <SkipBack className="w-4 h-4" />
                </button>

                <button
                  onClick={togglePlayPause}
                  className="p-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold transition-all shadow-md shadow-sky-500/20 active:scale-95"
                  title={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
                </button>

                <button
                  onClick={() =>
                    currentSentenceIndex < segments.length - 1 && handleSentenceClick(currentSentenceIndex + 1)
                  }
                  disabled={currentSentenceIndex >= segments.length - 1}
                  className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 rounded-lg hover:bg-slate-700 transition-colors"
                  title="Next line"
                >
                  <SkipForward className="w-4 h-4" />
                </button>

                <button
                  onClick={handleReplay}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-700 transition-colors"
                  title="Replay"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>

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
