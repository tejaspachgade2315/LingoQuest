'use client';

import React, { useEffect, useRef } from 'react';

export interface LiveKitVisualizerProps {
  volume?: number; // 0.0 to 1.0
  isSpeaking?: boolean;
  barCount?: number;
  color?: string;
  className?: string;
}

export const LiveKitVisualizer: React.FC<LiveKitVisualizerProps> = ({
  volume = 0,
  isSpeaking = false,
  barCount = 12,
  color = '#38bdf8',
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const barWidth = width / (barCount * 1.5);
      const gap = barWidth * 0.5;

      const baseIntensity = isSpeaking ? Math.max(volume, 0.25) : 0.08;

      for (let i = 0; i < barCount; i++) {
        const x = i * (barWidth + gap) + gap / 2;
        const wave = Math.sin(phase + i * 0.5) * 0.5 + 0.5;
        const barHeight = Math.max(4, height * baseIntensity * wave * (0.8 + Math.random() * 0.2));
        const y = (height - barHeight) / 2;

        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, '#818cf8');

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 4);
        ctx.fill();
      }

      phase += isSpeaking ? 0.2 : 0.05;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [volume, isSpeaking, barCount, color]);

  return (
    <div className={`relative flex items-center justify-center p-2 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md ${className}`}>
      <canvas
        ref={canvasRef}
        width={180}
        height={48}
        className="w-full h-12"
      />
      {isSpeaking && (
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
        </span>
      )}
    </div>
  );
};
