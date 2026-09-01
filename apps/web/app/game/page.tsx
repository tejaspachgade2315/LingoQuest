'use client';

import React, { useEffect, useState, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useLocalParticipant,
  useRoomContext,
} from '@livekit/components-react';
import { DataPacket_Kind, RoomEvent } from 'livekit-client';
import { ReadingBox } from '../../components/reading-box';
import {
  EvaluatedWord,
  SessionMetrics,
  VoiceAgentDataPacket,
  DdaMetrics,
  ComprehensionQuestion,
  ComprehensionEvaluation,
} from '@reading-game/shared-types';
import { ArrowLeft, PhoneOff, RefreshCw } from 'lucide-react';

// Single source of truth in sync with Python voice-worker STORY_CATALOG
const STORY_DATA: Record<string, { title: string; text: string }> = {
  'story-1': {
    title: 'The Brave Little Falcon',
    text: 'High above the rocky ridge a young falcon named Pip spread his wings.',
  },
  'story-2': {
    title: 'Echoes of the Deep Forest',
    text: 'Twilight painted the tall canopy in shades of violet and emerald.',
  },
  'story-3': {
    title: 'Journey to the Obsidian Spire',
    text: 'Turbulent currents crashed against the jagged obsidian cliffs.',
  },
};

function GameSessionRoom({
  storyId,
  user,
  avatar = '🦉',
  onLeave,
}: {
  storyId: string;
  user: string;
  avatar?: string;
  onLeave: () => void;
}) {
  const room = useRoomContext();
  const { localParticipant } = useLocalParticipant();
  const story = STORY_DATA[storyId] || STORY_DATA['story-1'];
  const [currentWords, setCurrentWords] = useState<string[]>(() => story.text.split(' '));
  const [sentenceNumber, setSentenceNumber] = useState(1);
  const [soundoutCue, setSoundoutCue] = useState<{ word: string; soundedOut: string } | undefined>();

  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [evaluatedWords, setEvaluatedWords] = useState<Record<number, EvaluatedWord>>({});
  const [heardSpeech, setHeardSpeech] = useState<string>('');
  const [feedbackCue, setFeedbackCue] = useState<string | undefined>(
    `Hi ${user}! Read the first glowing word out loud!`
  );
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [metrics, setMetrics] = useState<SessionMetrics>({
    totalWords: currentWords.length,
    correctWords: 0,
    imperfectWords: 0,
    missedWords: 0,
    accuracyPercentage: 100,
    wpm: 0,
    readingDurationSeconds: 0,
    streak: 0,
    highestStreak: 0,
    points: 0,
  });

  // Pedagogical DDA & Comprehension State
  const [ddaMetrics, setDdaMetrics] = useState<DdaMetrics | undefined>();
  const [comprehensionQuestion, setComprehensionQuestion] = useState<ComprehensionQuestion | undefined>();
  const [comprehensionEvaluation, setComprehensionEvaluation] = useState<ComprehensionEvaluation | undefined>();
  const [phonicsRule, setPhonicsRule] = useState<string | undefined>();

  // Listen for real-time LiveKit Data Channel messages from Python Voice Worker
  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (payload: Uint8Array, participant?: any, kind?: DataPacket_Kind) => {
      try {
        const decoded = new TextDecoder().decode(payload);
        const data: VoiceAgentDataPacket = JSON.parse(decoded);

        if (data.heardSpeech) {
          setHeardSpeech(data.heardSpeech);
        }

        if (data.type === 'word_highlight') {
          setCurrentWordIndex(data.currentWordIndex);
          setSoundoutCue(undefined); // clear hint when word advances
          if (data.evaluatedWord) {
            setEvaluatedWords((prev) => ({
              ...prev,
              [data.evaluatedWord!.index]: data.evaluatedWord!,
            }));
          }
          if (data.metrics) {
            setMetrics((prev) => ({ ...prev, ...data.metrics }));
          }
          if (data.feedbackText) {
            setFeedbackCue(data.feedbackText);
          }
        } else if (data.type === 'speech_transcribed_live') {
          if (data.heardSpeech) {
            setHeardSpeech(data.heardSpeech);
          }
        } else if (data.type === 'story_advanced') {
          if (data.words && data.words.length > 0) {
            setCurrentWords(data.words);
            setCurrentWordIndex(0);
            setEvaluatedWords({});
            setSentenceNumber((prev) => prev + 1);
            setSoundoutCue(undefined);
            setComprehensionQuestion(undefined);
            setComprehensionEvaluation(undefined);
            setPhonicsRule(undefined);
            setHeardSpeech('');
          }
          if (data.ddaMetrics) {
            setDdaMetrics(data.ddaMetrics);
          }
          if (data.feedbackText) {
            setFeedbackCue(data.feedbackText);
          }
          if (data.metrics) {
            setMetrics((prev) => ({ ...prev, ...data.metrics }));
          }
        } else if (data.type === 'hint_soundout') {
          if (data.word && data.soundedOut) {
            setSoundoutCue({ word: data.word, soundedOut: data.soundedOut });
          }
          if (data.feedbackText) {
            setFeedbackCue(data.feedbackText);
          }
        } else if (data.type === 'phonics_rule_intervention') {
          if (data.phonicsRule) {
            setPhonicsRule(data.phonicsRule);
          }
          if (data.ddaMetrics) {
            setDdaMetrics(data.ddaMetrics);
          }
        } else if (data.type === 'comprehension_question_prompt') {
          if (data.comprehensionQuestion) {
            setComprehensionQuestion(data.comprehensionQuestion);
            setComprehensionEvaluation(undefined);
          }
          if (data.ddaMetrics) {
            setDdaMetrics(data.ddaMetrics);
          }
          if (data.feedbackText) {
            setFeedbackCue(data.feedbackText);
          }
        } else if (data.type === 'comprehension_eval_result') {
          if (data.comprehensionEval) {
            setComprehensionEvaluation(data.comprehensionEval);
            if (data.comprehensionEval.bonusXp) {
              setMetrics((prev) => ({
                ...prev,
                points: (prev.points || 0) + data.comprehensionEval!.bonusXp,
              }));
            }
          }
          if (data.feedbackText) {
            setFeedbackCue(data.feedbackText);
          }
        } else if (data.type === 'agent_speech_state') {
          setIsAgentSpeaking(!!data.isAgentSpeaking);
        } else if (data.type === 'feedback_cue' && data.feedbackText) {
          setFeedbackCue(data.feedbackText);
        }
      } catch (err) {
        console.error('Failed to parse voice-worker data packet', err);
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room]);

  const toggleMic = useCallback(async () => {
    if (!localParticipant) return;
    const currentEnabled = localParticipant.isMicrophoneEnabled;
    await localParticipant.setMicrophoneEnabled(!currentEnabled);
    setIsMuted(currentEnabled);
  }, [localParticipant]);

  const requestSoundout = useCallback(() => {
    const currentWord = currentWords[currentWordIndex];
    if (!currentWord) return;

    // Send hint request to LiveKit agent
    if (room && room.localParticipant) {
      try {
        const payload = JSON.stringify({
          type: 'request_soundout',
          word: currentWord,
          wordIndex: currentWordIndex,
        });
        room.localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
      } catch (err) {
        console.error('Failed to publish soundout request', err);
      }
    }

    // Instant browser audio fallback
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(currentWord);
      utterance.rate = 0.85;
      window.speechSynthesis.speak(utterance);
    }
  }, [room, currentWords, currentWordIndex]);

  const skipCurrentWord = useCallback(() => {
    // Notify LiveKit agent to mark current word as missed and advance
    if (room && room.localParticipant) {
      try {
        const payload = JSON.stringify({ type: 'skip_word' });
        room.localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
      } catch (err) {
        console.error('Failed to send skip_word event', err);
      }
    }

    if (currentWordIndex < currentWords.length - 1) {
      setCurrentWordIndex((prev) => prev + 1);
    }
  }, [room, currentWordIndex, currentWords.length]);

  const skipComprehension = useCallback(() => {
    setComprehensionQuestion(undefined);
    setComprehensionEvaluation(undefined);
    if (room && room.localParticipant) {
      try {
        const payload = JSON.stringify({ type: 'skip_comprehension' });
        room.localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
      } catch (err) {
        console.error('Failed to skip comprehension checkpoint', err);
      }
    }
  }, [room]);

  const continueComprehension = useCallback(() => {
    setComprehensionQuestion(undefined);
    setComprehensionEvaluation(undefined);
  }, []);

  return (
    <div className="h-full flex flex-col justify-between overflow-hidden">
      {/* Top Header Bar (Compact, fits in view) */}
      <div className="h-10 sm:h-11 flex-shrink-0 glass-panel px-3 sm:px-5 rounded-2xl border border-white/10 flex items-center justify-between mb-2">
        {/* Back button + Story badge */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onLeave}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs flex items-center gap-1 transition-colors font-kids"
            title="Leave Quest"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Stories</span>
          </button>
          <div className="h-4 w-px bg-slate-800 hidden sm:block" />
          <span className="text-xs sm:text-sm font-extrabold text-white font-kids truncate max-w-[200px] sm:max-w-xs">
            {story.title}
          </span>
        </div>

        {/* Reader identity & Disconnect */}
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-slate-800/80 border border-white/5 text-xs font-bold text-slate-200 font-kids">
            <span>{avatar}</span>
            <span className="text-sky-300 truncate max-w-[120px]">{user}</span>
          </div>

          <button
            onClick={onLeave}
            className="p-1.5 rounded-xl bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 transition-colors"
            title="Exit Room"
          >
            <PhoneOff className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2-Column Storybook + AI Tutor Station Canvas */}
      <ReadingBox
        title={story.title}
        sentenceNumber={sentenceNumber}
        words={currentWords}
        currentWordIndex={currentWordIndex}
        evaluatedWords={evaluatedWords}
        metrics={metrics}
        ddaMetrics={ddaMetrics}
        feedbackCue={feedbackCue}
        soundoutCue={soundoutCue}
        phonicsRule={phonicsRule}
        comprehensionQuestion={comprehensionQuestion}
        comprehensionEvaluation={comprehensionEvaluation}
        heardSpeech={heardSpeech}
        isAgentSpeaking={isAgentSpeaking}
        isMuted={isMuted}
        onToggleMic={toggleMic}
        onRequestSoundout={requestSoundout}
        onSkipWord={skipCurrentWord}
        onSkipComprehension={skipComprehension}
        onContinueComprehension={continueComprehension}
        readerName={user}
        readerAvatar={avatar}
      />

      <RoomAudioRenderer />
    </div>
  );
}

function GameContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const storyId = searchParams.get('storyId') || 'story-1';
  const user = searchParams.get('user') || 'Hero Reader';
  const avatar = searchParams.get('avatar') || '🦉';

  // Stable single room name per session mount (avoids double room generation)
  const [roomName] = useState(() => `reading-session-${storyId}-${Date.now()}`);
  const [token, setToken] = useState<string | null>(null);
  const [serverUrl, setServerUrl] = useState<string>(
    process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880'
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchLiveKitToken() {
      try {
        setLoading(true);
        let apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        if (typeof window !== 'undefined' && apiUrl.includes('://api:')) {
          apiUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
        }

        let res: Response;
        try {
          res = await fetch(`${apiUrl}/api/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              roomName,
              participantName: user,
              metadata: { storyId, user, avatar },
            }),
          });
        } catch (fetchErr) {
          // Fallback to localhost:8000 directly
          res = await fetch('http://localhost:8000/api/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              roomName,
              participantName: user,
              metadata: { storyId, user, avatar },
            }),
          });
        }

        if (!res.ok) {
          throw new Error(`Token fetch failed with status: ${res.status}`);
        }

        const data = await res.json();
        if (isMounted) {
          setToken(data.token);
          if (data.serverUrl) {
            setServerUrl(data.serverUrl);
          }
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to connect to API server.');
          setLoading(false);
        }
      }
    }

    fetchLiveKitToken();

    return () => {
      isMounted = false;
    };
  }, [roomName, storyId, user, avatar]);

  const handleLeave = () => {
    router.push('/');
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4 font-kids">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-sky-400/20 border-t-sky-400 animate-spin" />
          <span className="text-2xl absolute inset-0 m-auto flex items-center justify-center animate-bounce">
            🦉
          </span>
        </div>
        <div className="text-center space-y-1">
          <p className="text-xl font-extrabold text-white">Opening Your Storybook...</p>
          <p className="text-xs text-sky-300 font-semibold">Sparky the AI Tutor is getting ready for you!</p>
        </div>
      </div>
    );
  }

  if (error && !token) {
    return (
      <div className="max-w-md mx-auto my-auto glass-panel p-6 sm:p-8 rounded-3xl border border-rose-500/30 text-center space-y-4 shadow-2xl font-kids">
        <div className="w-14 h-14 rounded-2xl bg-rose-500/15 text-rose-400 mx-auto flex items-center justify-center text-2xl">
          ⚠️
        </div>
        <h3 className="text-xl font-extrabold text-white">Oops! Connection Hiccup</h3>
        <p className="text-xs text-slate-300">
          We could not reach the reading room: <code className="text-rose-300">{error}</code>
        </p>
        <button
          onClick={() => window.location.reload()}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-black text-sm shadow-lg shadow-sky-500/20"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Try Again</span>
        </button>
      </div>
    );
  }

  return (
    <LiveKitRoom
      token={token!}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={handleLeave}
      className="h-full w-full overflow-hidden"
    >
      <GameSessionRoom storyId={storyId} user={user} avatar={avatar} onLeave={handleLeave} />
    </LiveKitRoom>
  );
}

export default function GamePage() {
  return (
    <Suspense
      fallback={
        <div className="h-full flex items-center justify-center">
          <div className="w-12 h-12 rounded-full border-4 border-sky-400/20 border-t-sky-400 animate-spin" />
        </div>
      }
    >
      <GameContent />
    </Suspense>
  );
}
