"use client";

import { useRef, useState } from "react";
import { PlayIcon } from "@/components/icons";

type Props = {
  role: "learner" | "tutor";
  text: string;
  latencyMs?: number;
  audioUrl?: string;
};

export default function ChatBubble({ role, text, latencyMs, audioUrl }: Props) {
  const isLearner = role === "learner";
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const hasAudio = !!audioUrl && !audioUrl.includes("/mock/");

  function handlePlay() {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  }

  return (
    <div className={`flex ${isLearner ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isLearner
            ? "bg-indigo-600 text-white"
            : "border border-gray-200 bg-white text-gray-900"
        }`}
      >
        {!isLearner && (
          <div className="mb-1 flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-600">LumiEdu</span>
            {latencyMs !== undefined && (
              <span className="text-xs text-gray-400">{latencyMs}ms</span>
            )}
            {hasAudio && (
              <button
                type="button"
                onClick={handlePlay}
                className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 hover:bg-indigo-200"
                title={isPlaying ? "Dung phat" : "Nghe phat am"}
              >
                <PlayIcon className="h-3 w-3" />
              </button>
            )}
          </div>
        )}
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{text}</p>
        {hasAudio && (
          <audio
            ref={audioRef}
            src={audioUrl}
            onEnded={() => setIsPlaying(false)}
            preload="none"
          />
        )}
      </div>
    </div>
  );
}
