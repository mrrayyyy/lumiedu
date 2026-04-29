"use client";

import { FormEvent, useRef } from "react";
import { MicrophoneIcon, SendIcon, SpinnerIcon, StopIcon } from "@/components/icons";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onVoiceStart: () => void;
  onVoiceStop: () => void;
  disabled: boolean;
  isRecording: boolean;
  isProcessingVoice: boolean;
};

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  onVoiceStart,
  onVoiceStop,
  disabled,
  isRecording,
  isProcessingVoice,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onSubmit();
    textareaRef.current?.focus();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-4">
      <form onSubmit={handleSubmit} className="mx-auto flex max-w-2xl gap-3">
        <button
          type="button"
          onClick={isRecording ? onVoiceStop : onVoiceStart}
          disabled={disabled || isProcessingVoice}
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-colors ${
            isRecording
              ? "animate-pulse bg-red-500 text-white hover:bg-red-600"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          } disabled:opacity-50`}
          title={isRecording ? "Dung ghi am" : "Ghi am giong noi"}
        >
          {isProcessingVoice ? (
            <SpinnerIcon className="h-5 w-5 animate-spin" />
          ) : isRecording ? (
            <StopIcon className="h-5 w-5" />
          ) : (
            <MicrophoneIcon className="h-5 w-5" />
          )}
        </button>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
          placeholder={isRecording ? "Dang ghi am..." : "Nhap cau hoi hoac nhan mic de noi..."}
          disabled={disabled || isRecording}
        />

        <button
          type="submit"
          disabled={disabled || !value.trim() || isRecording}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          <SendIcon />
        </button>
      </form>
      <p className="mx-auto mt-2 max-w-2xl text-center text-xs text-gray-400">
        {isRecording
          ? "Dang ghi am... Nhan nut do de dung va gui"
          : "Shift+Enter de xuong dong \u00b7 Nhan mic de noi \u00b7 LumiEdu day theo phuong phap Socratic"}
      </p>
    </div>
  );
}
