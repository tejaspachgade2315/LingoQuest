'use client';

import React from 'react';
import {
  WordStatus,
  EvaluatedWord,
  SessionMetrics,
  DdaMetrics,
  ComprehensionQuestion,
  ComprehensionEvaluation,
} from '@reading-game/shared-types';
import {
  Sparkles,
  Trophy,
  Award,
  CheckCircle2,
  Flame,
  Volume2,
  Wand2,
  Star,
  Mic,
  MicOff,
  SkipForward,
  HelpCircle,
  BookOpen,
} from 'lucide-react';
import { LiveKitVisualizer } from '@reading-game/ui';
import { ComprehensionCheckpoint } from './comprehension-checkpoint';

interface ReadingBoxProps {
  title: string;
  sentenceNumber?: number;
  words: string[];
  currentWordIndex: number;
  evaluatedWords: Record<number, EvaluatedWord>;
  metrics: SessionMetrics;
  ddaMetrics?: DdaMetrics;
  feedbackCue?: string;
  soundoutCue?: { word: string; soundedOut: string };
  phonicsRule?: string;
  comprehensionQuestion?: ComprehensionQuestion;
  comprehensionEvaluation?: ComprehensionEvaluation;
  heardSpeech?: string;
  isAgentSpeaking?: boolean;
  isMuted?: boolean;
  onToggleMic?: () => void;
  onRequestSoundout?: () => void;
  onSkipWord?: () => void;
  onSkipComprehension?: () => void;
  onContinueComprehension?: () => void;
  readerName?: string;
  readerAvatar?: string;
}

export const ReadingBox: React.FC<ReadingBoxProps> = ({
  title,
  sentenceNumber = 1,
  words,
  currentWordIndex,
  evaluatedWords,
  metrics,
  ddaMetrics,
  feedbackCue,
  soundoutCue,
  phonicsRule,
  comprehensionQuestion,
  comprehensionEvaluation,
  heardSpeech,
  isAgentSpeaking = false,
  isMuted = false,
  onToggleMic,
  onRequestSoundout,
  onSkipWord,
  onSkipComprehension,
  onContinueComprehension,
  readerName = 'Hero Reader',
  readerAvatar = '🦉',
}) => {
  const streak = metrics.streak || 0;
  const points = metrics.points || 0;
  const currentWord = words[currentWordIndex] || '';
  const progressPercent =
    words.length > 0
      ? Math.min(100, Math.round((currentWordIndex / words.length) * 100))
      : 0;

  // Split sounded out word into syllables/chips if available
  const phonemeChips = soundoutCue?.soundedOut
    ? soundoutCue.soundedOut.split(/[-\s]+/).filter(Boolean)
    : [];

  return (
    <div className="h-full flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-4 overflow-hidden relative">
      {/* 
        ========================================================================
        COLUMN 1 (LEFT ~62%): The Magical Storybook Canvas (NO SCROLLING)
        ========================================================================
      */}
      <div className="lg:col-span-7 xl:col-span-8 h-full flex flex-col justify-between glass-panel rounded-3xl p-4 sm:p-6 border border-white/10 shadow-2xl relative overflow-hidden">
        {/* Active Comprehension Checkpoint Overlay */}
        {comprehensionQuestion && (
          <ComprehensionCheckpoint
            question={comprehensionQuestion}
            evaluation={comprehensionEvaluation}
            isAgentSpeaking={isAgentSpeaking}
            onSkip={onSkipComprehension}
            onContinue={onContinueComprehension}
          />
        )}

        {/* Storybook Header & DDA Telemetry Badges */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10 flex-shrink-0">
          <div className="flex items-center space-x-2.5">
            <span className="text-2xl">📖</span>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-extrabold text-white font-kids tracking-wide leading-tight">
                  {title}
                </h2>
                {ddaMetrics && (
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider border font-kids ${
                      ddaMetrics.readingLevel === 'Independent'
                        ? 'bg-purple-500/20 text-purple-300 border-purple-400/40'
                        : ddaMetrics.readingLevel === 'Instructional'
                        ? 'bg-sky-500/20 text-sky-300 border-sky-400/40'
                        : 'bg-amber-500/20 text-amber-300 border-amber-400/40'
                    }`}
                  >
                    {ddaMetrics.readingLevel === 'Independent'
                      ? '🌟 Independent'
                      : ddaMetrics.readingLevel === 'Instructional'
                      ? '📘 Instructional'
                      : '🛡️ Phonics Support'}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
                  Quest Sentence #{sentenceNumber}
                </span>
                {ddaMetrics?.currentLexile && (
                  <>
                    <span className="text-slate-600 text-xs">•</span>
                    <span className="text-[11px] font-mono font-bold text-slate-300">
                      Lexile {ddaMetrics.currentLexile}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Progress Tracker with Star Icon */}
          <div className="flex items-center space-x-3">
            <div className="flex flex-col items-end">
              <span className="text-xs font-bold text-slate-300 font-kids">
                Word {Math.min(currentWordIndex + 1, words.length)} of {words.length}
              </span>
              <div className="w-24 sm:w-32 h-2 bg-slate-800 rounded-full mt-1 overflow-hidden border border-slate-700">
                <div
                  className="h-full bg-gradient-to-r from-amber-400 via-sky-400 to-emerald-400 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full font-extrabold bg-sky-500/20 text-sky-300 border border-sky-400/30 font-kids">
              {progressPercent}%
            </span>
          </div>
        </div>

        {/* Phonics Copilot Rule Alert (if active intervention) */}
        {phonicsRule && (
          <div className="p-2.5 sm:p-3 rounded-2xl bg-gradient-to-r from-purple-950/80 to-indigo-950/80 border border-purple-400/50 flex items-center space-x-3 my-1 animate-in slide-in-from-top-2 flex-shrink-0">
            <span className="text-2xl flex-shrink-0">🎓</span>
            <div className="min-w-0">
              <span className="text-[10px] font-black uppercase tracking-wider text-purple-300 block font-kids">
                Varsity Phonics Copilot Rule
              </span>
              <p className="text-xs font-bold text-white font-kids leading-snug line-clamp-2">
                {phonicsRule}
              </p>
            </div>
          </div>
        )}

        {/* 
          Main Story Text Flow:
          Large, rounded, kid-friendly font with clean spacing. Zero overlapping elements.
        */}
        <div className="flex-1 min-h-0 flex items-center justify-center py-2 sm:py-3">
          <div className="flex flex-wrap gap-x-3 sm:gap-x-4 gap-y-3 sm:gap-y-5 items-center justify-start text-2xl sm:text-3xl lg:text-4xl font-extrabold select-none font-kids leading-loose">
            {words.map((word, index) => {
              const isCurrent = index === currentWordIndex;
              const evaluation = evaluatedWords[index];
              const status: WordStatus = evaluation
                ? evaluation.status
                : isCurrent
                ? 'current'
                : 'idle';

              let baseClasses =
                'relative px-3.5 py-1.5 rounded-2xl transition-all duration-200 inline-flex items-center gap-1.5';

              // Successfully read word
              if (status === 'correct') {
                return (
                  <span
                    key={`${word}-${index}`}
                    id={`word-${index}`}
                    className={`${baseClasses} text-emerald-300 bg-emerald-500/15 border-2 border-emerald-400 shadow-sm shadow-emerald-500/20`}
                  >
                    {word}
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  </span>
                );
              }

              // Imperfect or close pronunciation
              if (status === 'imperfect') {
                return (
                  <span
                    key={`${word}-${index}`}
                    id={`word-${index}`}
                    className={`${baseClasses} text-amber-300 bg-amber-500/15 border-2 border-amber-400`}
                  >
                    {word}
                  </span>
                );
              }

              // Missed / Skipped word
              if (status === 'missed') {
                return (
                  <span
                    key={`${word}-${index}`}
                    id={`word-${index}`}
                    className={`${baseClasses} text-slate-400 bg-rose-500/10 border-2 border-rose-500/30 line-through opacity-70`}
                  >
                    {word}
                  </span>
                );
              }

              // Active Target Word (Luminous Halo Aura, subtle bottom indicator - ZERO OVERLAP)
              if (isCurrent) {
                return (
                  <span
                    key={`${word}-${index}`}
                    id={`word-${index}`}
                    className={`${baseClasses} text-white bg-sky-500/30 border-2 border-sky-400 word-halo ring-4 ring-sky-400/30 transform scale-105`}
                  >
                    {word}
                    <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 text-xs text-amber-400 animate-bounce">
                      ⭐
                    </span>
                  </span>
                );
              }

              // Idle upcoming word
              return (
                <span
                  key={`${word}-${index}`}
                  id={`word-${index}`}
                  className={`${baseClasses} text-slate-400/80 hover:text-slate-200 border-2 border-transparent`}
                >
                  {word}
                </span>
              );
            })}
          </div>
        </div>

        {/* Storybook Bottom: Phoneme Sound-Out Banner or Active Guidance Cue */}
        <div className="flex-shrink-0 pt-2 sm:pt-3 border-t border-white/10">
          {soundoutCue ? (
            <div className="p-3 sm:p-3.5 rounded-2xl bg-gradient-to-r from-amber-950/80 via-indigo-950/80 to-purple-950/80 border border-amber-400/40 flex items-center justify-between gap-3 shadow-lg animate-pulse">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">✨</span>
                <div>
                  <span className="text-[10px] font-black uppercase tracking-wider text-amber-400 block font-kids">
                    Phonics Sound-Out Helper
                  </span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-xs text-slate-300 font-bold">Say:</span>
                    {phonemeChips.length > 0 ? (
                      phonemeChips.map((chip, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-lg bg-black/50 text-amber-300 font-extrabold text-sm border border-amber-400/30 font-kids"
                        >
                          {chip}
                        </span>
                      ))
                    ) : (
                      <span className="text-amber-300 font-extrabold text-base font-kids">
                        {soundoutCue.soundedOut}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {onRequestSoundout && (
                <button
                  onClick={onRequestSoundout}
                  className="px-3 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs font-kids transition-transform active:scale-95 shadow-md flex items-center gap-1"
                >
                  <Volume2 className="w-3.5 h-3.5" />
                  <span>Hear Tutor</span>
                </button>
              )}
            </div>
          ) : (
            <div className="p-2.5 sm:p-3 rounded-2xl bg-slate-900/60 border border-white/5 flex items-center justify-between gap-3">
              <div className="flex items-center space-x-2.5 min-w-0 flex-1">
                <span className="text-xl flex-shrink-0">🎯</span>
                <div className="flex items-center gap-2 flex-wrap min-w-0">
                  <p className="text-xs sm:text-sm font-bold text-slate-200 font-kids">
                    Read aloud:{' '}
                    <span className="text-sky-300 text-sm sm:text-base underline underline-offset-4 font-black">
                      "{currentWord || 'Sentence Complete!'}"
                    </span>
                  </p>

                  {/* Real-time recognized speech preview indicator */}
                  {heardSpeech && (
                    <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-xl bg-purple-500/15 border border-purple-400/30 text-purple-200 text-xs font-mono">
                      <span className="text-purple-400 animate-pulse">🎙️</span>
                      <span className="font-bold text-slate-400 text-[10px]">Heard:</span>
                      <span className="italic text-purple-300 font-bold truncate max-w-[150px] sm:max-w-[200px]">
                        "{heardSpeech}"
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {onRequestSoundout && currentWord && (
                <button
                  onClick={onRequestSoundout}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-300 border border-slate-700 font-bold text-xs font-kids transition-all flex items-center gap-1.5 flex-shrink-0"
                >
                  <Volume2 className="w-3.5 h-3.5 text-amber-400" />
                  <span>Sound It Out</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 
        ========================================================================
        COLUMN 2 (RIGHT ~38%): AI Tutor Companion Station (NO SCROLLING)
        ========================================================================
      */}
      <div className="lg:col-span-5 xl:col-span-4 h-full flex flex-col justify-between glass-panel rounded-3xl p-4 sm:p-5 border border-white/10 shadow-2xl overflow-hidden">
        {/* Top: AI Companion Mascot & Speech Bubble */}
        <div className="flex-shrink-0 bg-slate-900/70 rounded-2xl p-3.5 border border-white/5 relative">
          <div className="flex items-center space-x-3 mb-2.5">
            <div className="relative">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center text-2xl shadow-lg shadow-sky-500/30">
                {isAgentSpeaking ? '🗣️' : '🦉'}
              </div>
              {isAgentSpeaking && (
                <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-purple-500"></span>
                </span>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-extrabold text-white font-kids">
                  Sparky the AI Tutor
                </h3>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-black uppercase ${
                    isAgentSpeaking
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-400/40 animate-pulse'
                      : 'bg-emerald-500/20 text-emerald-300'
                  }`}
                >
                  {isAgentSpeaking ? 'Speaking...' : 'Listening'}
                </span>
              </div>
              <p className="text-xs text-slate-300 line-clamp-2 mt-0.5 font-medium">
                {isAgentSpeaking
                  ? 'Listen to my guidance...'
                  : feedbackCue || "I'm listening! Speak clearly into your mic!"}
              </p>
            </div>
          </div>

          {/* Integrated Real-Time LiveKit Waveform Visualizer */}
          <LiveKitVisualizer
            isSpeaking={!isMuted || isAgentSpeaking}
            volume={isAgentSpeaking ? 0.8 : isMuted ? 0.05 : 0.45}
            color={isAgentSpeaking ? '#c084fc' : '#38bdf8'}
            barCount={14}
            className="w-full h-9 border-slate-800/80 bg-slate-950/80"
          />
        </div>

        {/* Center: Kid Gamification Scorecard (With WCPM Fluency Gauge) */}
        <div className="grid grid-cols-4 gap-1.5 sm:gap-2 my-2 flex-shrink-0">
          {/* XP Stars */}
          <div className="glass-card rounded-2xl p-2 flex flex-col items-center justify-center text-center border-amber-400/20 bg-amber-500/5">
            <span className="text-base sm:text-lg">⭐</span>
            <div className="text-[9px] font-bold text-slate-400 uppercase font-kids mt-0.5">
              Stars
            </div>
            <div className="text-sm sm:text-base font-black text-amber-300 font-mono leading-none mt-0.5">
              {points}
            </div>
          </div>

          {/* Streak Flame */}
          <div
            className={`glass-card rounded-2xl p-2 flex flex-col items-center justify-center text-center transition-all ${
              streak >= 3
                ? 'border-orange-500/40 bg-orange-500/15 shadow-md shadow-orange-500/20'
                : ''
            }`}
          >
            <span className={`text-base sm:text-lg ${streak >= 3 ? 'animate-bounce' : ''}`}>
              🔥
            </span>
            <div className="text-[9px] font-bold text-slate-400 uppercase font-kids mt-0.5">
              Streak
            </div>
            <div className="text-sm sm:text-base font-black text-white font-mono leading-none mt-0.5">
              {streak}x
            </div>
          </div>

          {/* Accuracy */}
          <div className="glass-card rounded-2xl p-2 flex flex-col items-center justify-center text-center border-emerald-400/20 bg-emerald-500/5">
            <span className="text-base sm:text-lg">🎯</span>
            <div className="text-[9px] font-bold text-slate-400 uppercase font-kids mt-0.5">
              Accuracy
            </div>
            <div className="text-sm sm:text-base font-black text-emerald-300 font-mono leading-none mt-0.5">
              {Math.round(metrics.accuracyPercentage || 100)}%
            </div>
          </div>

          {/* WCPM Fluency */}
          <div className="glass-card rounded-2xl p-2 flex flex-col items-center justify-center text-center border-sky-400/20 bg-sky-500/5">
            <span className="text-base sm:text-lg">⚡</span>
            <div className="text-[9px] font-bold text-slate-400 uppercase font-kids mt-0.5">
              WCPM
            </div>
            <div className="text-sm sm:text-base font-black text-sky-300 font-mono leading-none mt-0.5">
              {ddaMetrics?.wcpm || metrics.wpm || 0}
            </div>
          </div>
        </div>

        {/* 
          Bottom: Big Chunky Kid-Friendly Speak Button + Action Buttons
          Zero overlapping, prominent, intuitive for 7-year-olds!
        */}
        <div className="flex-shrink-0 flex flex-col gap-2 pt-2 border-t border-white/10">
          {/* Hero Speak Button */}
          {onToggleMic && (
            <button
              onClick={onToggleMic}
              className={`w-full py-3 sm:py-3.5 px-4 rounded-2xl font-extrabold text-sm sm:text-base flex items-center justify-center space-x-2.5 transition-all duration-200 transform active:scale-95 shadow-xl font-kids ${
                isMuted
                  ? 'bg-rose-500/20 text-rose-300 border-2 border-rose-500/40 hover:bg-rose-500/30'
                  : 'bg-gradient-to-r from-emerald-500 via-teal-500 to-sky-500 text-white shadow-emerald-500/25 ring-2 ring-emerald-400/50 hover:brightness-105'
              }`}
            >
              {isMuted ? (
                <>
                  <MicOff className="w-5 h-5 text-rose-400" />
                  <span>MIC MUTED - TAP TO READ</span>
                </>
              ) : (
                <>
                  <Mic className="w-5 h-5 text-white animate-pulse" />
                  <span>I'M LISTENING! READ ALOUD 🎙️</span>
                </>
              )}
            </button>
          )}

          {/* Secondary Action Row: Sound Out & Skip */}
          <div className="grid grid-cols-2 gap-2">
            {onRequestSoundout && (
              <button
                onClick={onRequestSoundout}
                className="py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 font-bold text-xs flex items-center justify-center space-x-1.5 transition-all shadow-sm font-kids"
              >
                <Volume2 className="w-4 h-4 text-amber-400" />
                <span>🔊 Sound Out</span>
              </button>
            )}

            {onSkipWord && (
              <button
                onClick={onSkipWord}
                className="py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-bold text-xs flex items-center justify-center space-x-1.5 transition-all shadow-sm font-kids"
              >
                <SkipForward className="w-4 h-4 text-sky-400" />
                <span>Next Word ⏭️</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
