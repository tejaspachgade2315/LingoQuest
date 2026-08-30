'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, ArrowRight, BookOpen, Star, Volume2 } from 'lucide-react';

const AVATARS = [
  { id: 'leo', name: 'Leo the Brave', emoji: '🦁', color: 'from-amber-500 to-orange-500' },
  { id: 'pip', name: 'Pip the Owl', emoji: '🦉', color: 'from-sky-400 to-blue-600' },
  { id: 'felix', name: 'Felix Fox', emoji: '🦊', color: 'from-orange-400 to-rose-500' },
  { id: 'sparky', name: 'Sparky Dragon', emoji: '🐉', color: 'from-emerald-400 to-teal-600' },
  { id: 'luna', name: 'Luna Unicorn', emoji: '🦄', color: 'from-fuchsia-400 to-purple-600' },
];

const SAMPLE_STORIES = [
  {
    id: 'story-1',
    title: 'The Brave Little Falcon',
    difficulty: 'Beginner',
    levelStars: 1,
    badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    icon: '🦅',
    wordsCount: 14,
    excerpt: 'High above the rocky ridge a young falcon named Pip spread his wings.',
  },
  {
    id: 'story-2',
    title: 'Echoes of the Deep Forest',
    difficulty: 'Explorer',
    levelStars: 2,
    badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    icon: '🌲',
    wordsCount: 12,
    excerpt: 'Twilight painted the tall canopy in shades of violet and emerald.',
  },
  {
    id: 'story-3',
    title: 'Journey to the Obsidian Spire',
    difficulty: 'Champion',
    levelStars: 3,
    badgeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
    icon: '✨',
    wordsCount: 10,
    excerpt: 'Turbulent currents crashed against the jagged obsidian cliffs.',
  },
];

export default function HomePage() {
  const router = useRouter();
  const [selectedAvatar, setSelectedAvatar] = useState(AVATARS[0]);
  const [userName, setUserName] = useState(AVATARS[0].name);
  const [selectedStory, setSelectedStory] = useState('story-1');

  const handleStartGame = (e: React.FormEvent) => {
    e.preventDefault();
    const finalName = userName.trim() || selectedAvatar.name;
    router.push(
      `/game?storyId=${selectedStory}&user=${encodeURIComponent(finalName)}&avatar=${selectedAvatar.emoji}`
    );
  };

  return (
    <div className="flex-1 flex flex-col justify-center py-2 sm:py-6">
      {/* Hero Welcome Header */}
      <div className="text-center max-w-3xl mx-auto mb-6 sm:mb-8">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-sky-500/15 border border-sky-400/30 text-sky-300 text-xs font-bold mb-3 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Real-Time Voice AI Reading Companion for Ages 7+</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white font-kids">
          Choose Your Buddy & <span className="text-gradient">Read Aloud!</span> 🌟
        </h1>
        <p className="text-slate-300 text-xs sm:text-sm max-w-xl mx-auto mt-2 font-medium">
          Speak into your microphone. Our friendly AI tutor listens, highlights words live, and helps you sound them out!
        </p>
      </div>

      {/* Main 2-Column Action Station (NO OVERLAPPING) */}
      <form
        onSubmit={handleStartGame}
        className="glass-panel rounded-3xl p-5 sm:p-8 border border-white/10 shadow-2xl max-w-5xl mx-auto w-full"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8 items-start">
          {/* LEFT COLUMN: Character Avatar Selection + Reader Name (5 cols) */}
          <div className="lg:col-span-5 flex flex-col space-y-4">
            <div>
              <label className="block text-sm font-bold text-amber-300 mb-2 uppercase tracking-wider font-kids">
                1. Pick Your Character:
              </label>
              <div className="grid grid-cols-5 gap-2">
                {AVATARS.map((av) => {
                  const isSelected = selectedAvatar.id === av.id;
                  return (
                    <button
                      type="button"
                      key={av.id}
                      onClick={() => {
                        setSelectedAvatar(av);
                        const isDefaultOrEmpty = !userName.trim() || AVATARS.some((a) => a.name === userName);
                        if (isDefaultOrEmpty) {
                          setUserName(av.name);
                        }
                      }}
                      className={`flex flex-col items-center justify-center p-2 sm:p-2.5 rounded-2xl border transition-all duration-200 transform hover:scale-105 active:scale-95 ${
                        isSelected
                          ? 'bg-sky-500/25 border-sky-400 ring-2 ring-sky-400 scale-105 shadow-lg shadow-sky-500/30'
                          : 'bg-slate-800/60 border-slate-700/80 hover:bg-slate-800 text-slate-400'
                      }`}
                    >
                      <span className="text-2xl sm:text-3xl mb-1">{av.emoji}</span>
                      <span className="text-[10px] font-bold text-white truncate max-w-full font-kids">
                        {av.name.split(' ')[0]}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Reader Name Input Box */}
            <div>
              <label className="block text-sm font-bold text-slate-200 mb-1.5 font-kids">
                Reader Name:
              </label>
              <input
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder={`Enter reader name (or play as ${selectedAvatar.name})`}
                className="w-full px-4 py-3 rounded-2xl bg-slate-900/90 border-2 border-slate-700 text-white font-bold placeholder-slate-500 focus:outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-500/20 transition-all font-kids text-base"
              />
            </div>

            {/* Selected Profile Preview Badge */}
            <div className="p-3 rounded-2xl bg-slate-800/50 border border-white/5 flex items-center space-x-3">
              <span className="text-3xl">{selectedAvatar.emoji}</span>
              <div>
                <div className="text-xs text-slate-400 font-kids">Ready to explore as:</div>
                <div className="text-sm font-extrabold text-sky-300 font-kids">
                  {userName || selectedAvatar.name}
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Story Quest Selection + Big Launch Button (7 cols) */}
          <div className="lg:col-span-7 flex flex-col space-y-4">
            <label className="block text-sm font-bold text-sky-300 mb-1 uppercase tracking-wider font-kids">
              2. Choose Your Story Quest:
            </label>
            <div className="space-y-2.5">
              {SAMPLE_STORIES.map((story) => {
                const isSelected = selectedStory === story.id;
                return (
                  <div
                    key={story.id}
                    onClick={() => setSelectedStory(story.id)}
                    className={`cursor-pointer p-3 sm:p-3.5 rounded-2xl border transition-all duration-200 flex items-center justify-between gap-3 ${
                      isSelected
                        ? 'bg-gradient-to-r from-sky-950/70 to-indigo-950/80 border-sky-400 ring-2 ring-sky-400/40 shadow-xl shadow-sky-500/20'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <span className="text-2xl p-2 rounded-xl bg-slate-800/80 border border-white/5 flex-shrink-0">
                        {story.icon}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-extrabold text-white text-sm sm:text-base font-kids truncate">
                            {story.title}
                          </h3>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase border whitespace-nowrap ${story.badgeColor}`}
                          >
                            {story.difficulty}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 line-clamp-1 mt-0.5 font-medium">
                          {story.excerpt}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 flex-shrink-0 text-amber-400">
                      {Array.from({ length: story.levelStars }).map((_, i) => (
                        <Star key={i} className="w-3.5 h-3.5 fill-amber-400" />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Big Launch Button */}
            <div className="pt-2">
              <button
                type="submit"
                className="w-full flex items-center justify-center space-x-3 py-3.5 sm:py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-500 via-sky-500 to-indigo-600 hover:from-emerald-400 hover:to-indigo-500 text-white font-extrabold text-base sm:text-lg shadow-xl shadow-sky-500/30 transition-all duration-200 transform hover:scale-[1.01] active:scale-[0.99] font-kids"
              >
                <span>{selectedAvatar.emoji}</span>
                <span>START READING QUEST!</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Reassurance Badges Footer */}
      <div className="flex items-center justify-center space-x-4 sm:space-x-8 text-xs font-bold text-slate-400 mt-6 text-center">
        <span className="flex items-center gap-1.5 text-sky-400">
          <Volume2 className="w-3.5 h-3.5" /> Instant AI Voice Feedback
        </span>
        <span>•</span>
        <span className="text-amber-400">✨ Automatic Phoneme Sound-Outs</span>
        <span>•</span>
        <span className="text-emerald-400">🎮 Generative Story Adventures</span>
      </div>
    </div>
  );
}
