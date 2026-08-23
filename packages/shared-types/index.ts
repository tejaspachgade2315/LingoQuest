/**
 * Game State DTOs and Shared Event Types
 */

export type WordStatus = 'idle' | 'current' | 'correct' | 'imperfect' | 'missed';

export interface EvaluatedWord {
  index: number;
  word: string;
  normalized: string;
  phoneticCode?: string;
  status: WordStatus;
  similarityScore: number;
  spokenAlternative?: string;
  timestampMs?: number;
  audioStartTime?: number;
  audioEndTime?: number;
}

export interface Passage {
  id: string;
  title: string;
  content: string;
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced';
  targetWpm?: number;
  words: string[];
  totalWords: number;
}

export interface GameSession {
  sessionId: string;
  passageId: string;
  userId: string;
  channel: 'web' | 'whatsapp' | 'telephony';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  currentWordIndex: number;
  accuracyScore: number;
  wordsReadCount: number;
  durationSeconds: number;
  createdAt: string;
  completedAt?: string;
}

export interface SessionMetrics {
  totalWords: number;
  correctWords: number;
  imperfectWords: number;
  missedWords: number;
  accuracyPercentage: number;
  wpm: number;
  readingDurationSeconds: number;
  streak?: number;
  highestStreak?: number;
  points?: number;
}

export type ReadingLevel = 'Independent' | 'Instructional' | 'Frustrational';

export interface DdaMetrics {
  wcpm: number;
  accuracyPercentage: number;
  currentLexile: string;
  targetVocabulary?: string[];
  readingLevel: ReadingLevel;
  strugglingWords: string[];
  sentencesRead: number;
}

export interface ComprehensionQuestion {
  id: string;
  question: string;
  targetConcept?: string;
  storyContext?: string;
}

export interface ComprehensionEvaluation {
  score: number; // 1 to 5 stars
  passed: boolean;
  tutorFeedback: string;
  bonusXp: number;
  childAnswer?: string;
}

export interface VoiceAgentDataPacket {
  type:
    | 'word_highlight'
    | 'agent_speech_state'
    | 'session_completed'
    | 'feedback_cue'
    | 'hint_soundout'
    | 'story_advanced'
    | 'comprehension_question_prompt'
    | 'comprehension_eval_result'
    | 'phonics_rule_intervention'
    | 'scene_visual_update'
    | 'speech_transcribed_live';
  sessionId: string;
  currentWordIndex: number;
  evaluatedWord?: EvaluatedWord;
  metrics?: Partial<SessionMetrics>;
  feedbackText?: string;
  heardSpeech?: string;
  isAgentSpeaking?: boolean;
  sentence?: string;
  words?: string[];
  word?: string;
  soundedOut?: string;
  comprehensionQuestion?: ComprehensionQuestion;
  comprehensionEval?: ComprehensionEvaluation;
  phonicsRule?: string;
  ddaMetrics?: DdaMetrics;
  scenePrompt?: string;
}

export interface LiveKitTokenRequest {
  roomName: string;
  participantName: string;
  metadata?: Record<string, string>;
}

export interface LiveKitTokenResponse {
  token: string;
  serverUrl: string;
  roomName: string;
  participantIdentity: string;
}
