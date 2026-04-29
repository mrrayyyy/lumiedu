"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { endSession, getSession, submitTurn } from "@/lib/api";
import type { Session, Turn } from "@/lib/types";
import ChatBubble from "@/components/chat/chat-bubble";
import ChatInput from "@/components/chat/chat-input";
import SessionHeader from "@/components/chat/session-header";
import TypingIndicator from "@/components/chat/typing-indicator";
import LoadingSpinner from "@/components/ui/loading-spinner";

type ChatMessage = {
  role: "learner" | "tutor";
  text: string;
  latencyMs?: number;
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

  async function handleSend() {
    const text = inputText.trim();
    if (!text || !session || isSending) return;

    setInputText("");
    setIsSending(true);
    setMessages((prev) => [...prev, { role: "learner", text }]);

    try {
      const result: Turn = await submitTurn(token, session.session_id, text);
      setMessages((prev) => [
        ...prev,
        { role: "tutor", text: result.assistant_response, latencyMs: result.response_ms },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "tutor", text: "Xin loi, co loi xay ra. Con thu lai nhe!" },
      ]);
    } finally {
      setIsSending(false);
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

  if (!session) return <LoadingSpinner message="Dang tai phien hoc..." />;

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <SessionHeader
        topic={session.lesson_topic}
        learnerId={session.learner_id}
        wsStatus={wsStatus}
        onEnd={handleEndSession}
      />

      <div className="flex-1 overflow-auto px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.map((msg, idx) => (
            <ChatBubble
              key={`msg-${msg.role}-${idx}`}
              role={msg.role}
              text={msg.text}
              latencyMs={msg.latencyMs}
            />
          ))}
          {isSending && <TypingIndicator />}
          <div ref={chatEndRef} />
        </div>
      </div>

      <ChatInput
        value={inputText}
        onChange={setInputText}
        onSubmit={handleSend}
        disabled={isSending}
      />
    </div>
  );
}

export default function SessionPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <SessionContent />
    </Suspense>
  );
}
