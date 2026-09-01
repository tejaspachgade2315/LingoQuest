'use client';

import React from 'react';
import { ComprehensionQuestion, ComprehensionEvaluation } from '@reading-game/shared-types';
import { Sparkles, Star, Mic, ArrowRight, CheckCircle2, Award, Volume2, HelpCircle } from 'lucide-react';
import { LiveKitVisualizer } from '@reading-game/ui';

interface ComprehensionCheckpointProps {
  question: ComprehensionQuestion;
  evaluation?: ComprehensionEvaluation;
  isAgentSpeaking?: boolean;
  onSkip?: () => void;
  onContinue?: () => void;
}

export const ComprehensionCheckpoint: React.FC<ComprehensionCheckpointProps> = ({
  question,
  evaluation,
  isAgentSpeaking = false,
  onSkip,
  onContinue,
}) => {
  const isEvaluated = !!evaluation;

  return (
    <div className="absolute inset-0 z-30 bg-slate-950/95 backdrop-blur-xl rounded-3xl p-5 sm:p-7 flex flex-col justify-between border-2 border-amber-400/40 shadow-2xl animate-in fade-in zoom-in-95 duration-300 font-kids">
      {/* Top Header Badge */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-400 to-orange-500 flex items-center justify-center text-xl shadow-lg shadow-amber-500/30">
            🔍
          </div>
          <div>
            <span className="text-[10px] font-black tracking-widest uppercase text-amber-400 block">
              Varsity Reading Copilot
            </span>
            <h2 className="text-lg sm:text-xl font-extrabold text-white tracking-wide leading-tight">
              Story Detective Checkpoint!
            </h2>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-400/30">
            Plot Comprehension
          </span>
          {onSkip && !isEvaluated && (
            <button
              onClick={onSkip}
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors px-2 py-1"
            >
              Skip
            </button>
          )}
        </div>
      </div>

      {/* Main Center Content: Question OR Evaluation Result */}
      <div className="flex-1 min-h-0 flex flex-col items-center justify-center py-4 text-center">
        {!isEvaluated ? (
          /* Active Question & Listening State */
          <div className="max-w-xl mx-auto space-y-4">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-sky-500/15 border border-sky-400/30 text-sky-300 text-xs font-bold animate-pulse">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Sparky wants to know your thoughts!</span>
            </div>

            {/* Question in Large Kid Font */}
            <h3 className="text-xl sm:text-3xl font-extrabold text-white leading-snug">
              "{question.question}"
            </h3>

            {/* Live Listening Waveform */}
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-white/10 flex flex-col items-center space-y-2">
              <div className="flex items-center space-x-2 text-xs font-bold text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <span>Microphone active • Speak your answer freely!</span>
              </div>
              <LiveKitVisualizer
                isSpeaking={true}
                volume={0.5}
                color="#38bdf8"
                barCount={16}
                className="w-full max-w-xs h-10 border-slate-800 bg-slate-950"
              />
              <p className="text-[11px] text-slate-400">
                Answer using your normal speaking voice. Sparky is listening to your explanation!
              </p>
            </div>
          </div>
        ) : (
          /* Evaluation Result State */
          <div className="max-w-xl mx-auto space-y-4 animate-in zoom-in-95 duration-300">
            {/* Star Rating Badge */}
            <div className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-2xl bg-amber-500/20 border-2 border-amber-400 shadow-lg shadow-amber-500/20">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`w-6 h-6 ${
                    i < evaluation.score
                      ? 'fill-amber-400 text-amber-400 animate-bounce'
                      : 'text-slate-600'
                  }`}
                />
              ))}
            </div>

            <h3 className="text-2xl sm:text-3xl font-black text-white">
              {evaluation.passed ? 'Super Detective Score!' : 'Great Effort!'}
            </h3>

            {/* Sparky Tutor Feedback */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-sky-950/70 to-indigo-950/70 border border-sky-400/40 text-left flex items-start space-x-3">
              <span className="text-3xl flex-shrink-0">🦉</span>
              <div>
                <span className="text-[10px] font-black uppercase tracking-wider text-sky-400 block">
                  Sparky the Tutor says:
                </span>
                <p className="text-sm sm:text-base font-bold text-slate-100 mt-0.5 leading-relaxed">
                  "{evaluation.tutorFeedback}"
                </p>
              </div>
            </div>

            {/* Bonus XP Awarded */}
            <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 font-extrabold text-sm shadow-md">
              <Award className="w-4 h-4 text-emerald-400" />
              <span>+{evaluation.bonusXp} Detective Star XP Earned!</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer Action */}
      <div className="flex-shrink-0 pt-3 border-t border-white/10 flex items-center justify-between">
        <span className="text-xs text-slate-400 font-medium">
          {isEvaluated
            ? 'Resuming your reading quest with adaptive difficulty...'
            : 'Take your time — there are no wrong answers in storytelling!'}
        </span>

        {isEvaluated && onContinue && (
          <button
            onClick={onContinue}
            className="px-5 py-2.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-sky-500 hover:from-emerald-400 hover:to-sky-400 text-white font-extrabold text-sm shadow-lg shadow-emerald-500/30 transition-all transform hover:scale-105 active:scale-95 flex items-center gap-1.5"
          >
            <span>Continue Quest</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
