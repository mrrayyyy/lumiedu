"use client";

import { FormEvent, useRef } from "react";
import { SendIcon } from "@/components/icons";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
};

export default function ChatInput({ value, onChange, onSubmit, disabled }: Props) {
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
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
          placeholder="Nhap cau hoi Toan lop 6... (Enter de gui)"
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          <SendIcon />
        </button>
      </form>
      <p className="mx-auto mt-2 max-w-2xl text-center text-xs text-gray-400">
        Shift+Enter de xuong dong &middot; LumiEdu day theo phuong phap Socratic
      </p>
    </div>
  );
}
