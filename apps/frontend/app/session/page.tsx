"use client";

import { FormEvent, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { endSession, getSession, submitTurn } from "@/lib/api";
import type { Session, Turn } from "@/lib/types";

type ChatMessage = {
  role: "learner" | "tutor";
  text: string;
  latencyMs?: number;
  timestamp: Date;
};

function SessionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("id") ?? "";
  const { token, isAuthenticated } = useAuth();

  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (!sessionId) {
      router.push("/dashboard");
      return;
    }

    getSession(token, sessionId)
      .then((s) => {
        setSession(s);
        setMessages([
          {
            role: "tutor",
            text: `Chao con! Hom nay minh se hoc ve "${s.lesson_topic}" nhe. Con co bai nao can minh ho tro khong?`,
            timestamp: new Date(),
          },
        ]);
      })
      .catch(() => {
        setError("Khong the tai phien hoc");
      });
  }, [isAuthenticated, router, sessionId, token]);

  useEffect(() => {
    if (!session || !token) return;

    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(
      `${wsProtocol}://${window.location.host}/api/v1/sessions/${session.session_id}/ws?token=${encodeURIComponent(token)}`,
    );

    ws.onopen = () => {
      setWsStatus("connected");
      ws.send("ping");
    };
    ws.onclose = () => setWsStatus("disconnected");
    ws.onerror = () => setWsStatus("disconnected");

    return () => ws.close();
  }, [session, token]);

  useEffect(scrollToBottom, [messages, scrollToBottom]);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const text = inputText.trim();
    if (!text || !session || isSending) return;

    setInputText("");
    setIsSending(true);
    setMessages((prev) => [
      ...prev,
      { role: "learner", text, timestamp: new Date() },
    ]);

    try {
      const result: Turn = await submitTurn(token, session.session_id, text);
      setMessages((prev) => [
        ...prev,
        {
          role: "tutor",
          text: result.assistant_response,
          latencyMs: result.response_ms,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "tutor",
          text: "Xin loi, co loi xay ra. Con thu lai nhe!",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsSending(false);
      textareaRef.current?.focus();
    }
  }

  async function handleEndSession() {
    if (!session) return;
    try {
      await endSession(token, session.session_id);
      router.push("/dashboard");
    } catch {
      setError("Khong the ket thuc phien hoc");
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const form = e.currentTarget.form;
      if (form) form.requestSubmit();
    }
  }

  if (!isAuthenticated) return null;

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <Link href="/dashboard" className="mt-4 inline-block text-indigo-600 hover:underline">
            Quay lai trang chu
          </Link>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="flex items-center gap-3 text-gray-500">
          <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Dang tai phien hoc...
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <h1 className="font-semibold text-gray-900">{session.lesson_topic}</h1>
            <p className="text-xs text-gray-500">
              Hoc sinh: {session.learner_id}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`flex items-center gap-1.5 text-xs ${
              wsStatus === "connected" ? "text-emerald-600" : "text-gray-400"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                wsStatus === "connected" ? "bg-emerald-500" : "bg-gray-300"
              }`}
            />
            {wsStatus === "connected" ? "Ket noi" : "Ngat ket noi"}
          </span>
          <button
            type="button"
            onClick={handleEndSession}
            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
          >
            Ket thuc
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-auto px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={`msg-${msg.role}-${idx}`}
              className={`flex ${msg.role === "learner" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === "learner"
                    ? "bg-indigo-600 text-white"
                    : "border border-gray-200 bg-white text-gray-900"
                }`}
              >
                {msg.role === "tutor" && (
                  <div className="mb-1 flex items-center gap-2">
                    <span className="text-xs font-semibold text-indigo-600">
                      LumiEdu
                    </span>
                    {msg.latencyMs !== undefined && (
                      <span className="text-xs text-gray-400">
                        {msg.latencyMs}ms
                      </span>
                    )}
                  </div>
                )}
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.text}
                </p>
              </div>
            </div>
          ))}

          {isSending && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-gray-200 bg-white px-4 py-3">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-indigo-600">LumiEdu</span>
                  <span className="text-xs text-gray-400">dang suy nghi...</span>
                </div>
                <div className="mt-2 flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "0ms" }} />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "150ms" }} />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="border-t border-gray-200 bg-white px-4 py-4">
        <form onSubmit={handleSubmit} className="mx-auto flex max-w-2xl gap-3">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
            placeholder="Nhap cau hoi Toan lop 6... (Enter de gui)"
            disabled={isSending}
          />
          <button
            type="submit"
            disabled={isSending || !inputText.trim()}
            className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0l-7 7m7-7l7 7" />
            </svg>
          </button>
        </form>
        <p className="mx-auto mt-2 max-w-2xl text-center text-xs text-gray-400">
          Shift+Enter de xuong dong &middot; LumiEdu day theo phuong phap Socratic
        </p>
      </div>
    </div>
  );
}

export default function SessionPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <p className="text-gray-500">Dang tai...</p>
        </div>
      }
    >
      <SessionContent />
    </Suspense>
  );
}
