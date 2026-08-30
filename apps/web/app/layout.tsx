import type { Metadata } from 'next';
import './globals.css';
import '@livekit/components-styles';

export const metadata: Metadata = {
  title: 'LingoQuest Kids | Real-Time Voice Reading Game',
  description: 'A magical voice-driven reading tutor for young learners. Read aloud and explore enchanted stories!',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark min-h-full">
      <body className="min-h-screen bg-[#060913] text-slate-100 antialiased selection:bg-sky-500/30 selection:text-sky-200 flex flex-col">
        {/* Ambient background glows */}
        <div className="fixed inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(56,189,248,0.18),rgba(0,0,0,0))] pointer-events-none" />
        <div className="fixed -bottom-40 -left-40 w-96 h-96 rounded-full bg-purple-600/10 blur-3xl pointer-events-none" />
        <div className="fixed -bottom-40 -right-40 w-96 h-96 rounded-full bg-emerald-600/10 blur-3xl pointer-events-none" />

        {/* Compact Kid Header */}
        <header className="relative z-30 h-14 glass-panel border-b border-white/10 px-4 sm:px-6 flex items-center justify-between flex-shrink-0">
          <a href="/" className="flex items-center space-x-2.5 group">
            <div className="h-9 w-9 rounded-2xl bg-gradient-to-tr from-sky-400 via-indigo-500 to-amber-400 flex items-center justify-center text-xl shadow-lg shadow-sky-500/25 group-hover:scale-105 transition-transform">
              🦉
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-lg sm:text-xl tracking-tight text-gradient leading-tight font-kids">
                LingoQuest
              </span>
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest leading-none">
                Kids Reading Studio
              </span>
            </div>
          </a>

          <nav className="flex items-center space-x-3 sm:space-x-5 text-sm font-bold">
            <a 
              href="/" 
              className="px-3 py-1 rounded-xl text-slate-300 hover:text-white hover:bg-white/5 transition-all text-xs sm:text-sm font-kids"
            >
              📚 Stories
            </a>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm font-kids">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              AI Tutor Ready
            </span>
          </nav>
        </header>

        {/* Main Container */}
        <main className="relative z-10 flex-1 flex flex-col p-3 sm:p-6 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </body>
    </html>
  );
}
