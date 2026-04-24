"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Session = {
  session_id: string;
  learner_id: string;
  lesson_topic: string;
  status: string;
};

type Turn = {
  transcript: string;
  assistant_response: string;
  response_ms: number;
};

type Progress = {
  turns: number;
  avgLatencyMs: number;
};

type Metrics = {
  turn_total: number;
  turn_error_total: number;
  e2e_latency_ms_last: number;
};

const API_BASE = "/api";

export default function Home() {
  const [learnerId, setLearnerId] = useState("student-demo");
  const [lessonTopic, setLessonTopic] = useState("Phan so lop 6");
  const [session, setSession] = useState<Session | null>(null);
  const [inputText, setInputText] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [events, setEvents] = useState<string[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [email, setEmail] = useState("admin@lumiedu.local");
  const [password, setPassword] = useState("Admin123!");
  const [token, setToken] = useState("");
  const [metrics, setMetrics] = useState<Metrics>({
    turn_total: 0,
    turn_error_total: 0,
    e2e_latency_ms_last: 0,
  });

  const progress: Progress = useMemo(() => {
    const turnsCount = turns.length;
    const totalLatency = turns.reduce((acc, turn) => acc + turn.response_ms, 0);
    return {
      turns: turnsCount,
      avgLatencyMs: turnsCount === 0 ? 0 : Math.round(totalLatency / turnsCount),
    };
  }, [turns]);

  useEffect(() => {
    if (!session || !token) {
      return;
    }

    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(
      `${wsProtocol}://${window.location.host}${API_BASE}/v1/sessions/${session.session_id}/ws?token=${encodeURIComponent(token)}`,
    );
    ws.onopen = () => {
      ws.send("ping");
    };
    ws.onmessage = (event) => {
      setEvents((prev) => [...prev.slice(-7), event.data]);
    };
    ws.onerror = () => {
      setEvents((prev) => [...prev.slice(-7), "ws_error"]);
    };

    return () => ws.close();
  }, [session, token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    const interval = window.setInterval(async () => {
      const response = await fetch(`${API_BASE}/metrics`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = (await response.json()) as Metrics;
        setMetrics(data);
      }
    }, 3000);

    return () => window.clearInterval(interval);
  }, [token]);

  async function login() {
    const response = await fetch(`${API_BASE}/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      throw new Error("Login failed");
    }
    const data = (await response.json()) as { access_token: string };
    setToken(data.access_token);
  }

  async function startSession() {
    const response = await fetch(`${API_BASE}/v1/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ learner_id: learnerId, lesson_topic: lessonTopic }),
    });
    if (!response.ok) {
      throw new Error("Failed to create session");
    }
    const createdSession = (await response.json()) as Session;
    setSession(createdSession);
    setTurns([]);
    setEvents(["session_started"]);
  }

  async function submitTurn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session || !inputText.trim()) {
      return;
    }

    setIsSending(true);
    try {
      const response = await fetch(`${API_BASE}/v1/sessions/${session.session_id}/turns`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text_input: inputText }),
      });
      if (!response.ok) {
        throw new Error("Turn request failed");
      }
      const data = (await response.json()) as Turn;
      setTurns((prev) => [...prev, data]);
      setInputText("");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6">
      <h1 className="text-3xl font-bold">LumiEdu Voice-First Tutor MVP</h1>

      <section className="grid gap-3 rounded border p-4">
        <h2 className="text-xl font-semibold">Authentication</h2>
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="rounded border px-3 py-2"
          placeholder="Admin email"
        />
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded border px-3 py-2"
          type="password"
          placeholder="Password"
        />
        <button
          type="button"
          onClick={login}
          className="w-fit rounded bg-indigo-600 px-4 py-2 text-white disabled:opacity-50"
          disabled={!email || !password}
        >
          Sign in
        </button>
        <p className="text-xs text-gray-500">{token ? "Authenticated" : "Not authenticated"}</p>
      </section>

      <section className="grid gap-3 rounded border p-4">
        <h2 className="text-xl font-semibold">Session Control</h2>
        <input
          value={learnerId}
          onChange={(event) => setLearnerId(event.target.value)}
          className="rounded border px-3 py-2"
          placeholder="Learner ID"
        />
        <input
          value={lessonTopic}
          onChange={(event) => setLessonTopic(event.target.value)}
          className="rounded border px-3 py-2"
          placeholder="Lesson topic"
        />
        <button
          type="button"
          onClick={startSession}
          className="w-fit rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
          disabled={!token || !learnerId || !lessonTopic}
        >
          Start Learning Session
        </button>
        {session && <p className="text-sm">Active session: {session.session_id}</p>}
      </section>

      <section className="grid gap-3 rounded border p-4">
        <h2 className="text-xl font-semibold">Voice Loop (MVP text simulation)</h2>
        <form className="flex flex-col gap-3" onSubmit={submitTurn}>
          <textarea
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            className="min-h-24 rounded border px-3 py-2"
            placeholder="Nhap cau hoi Toan lop 6..."
          />
          <button
            type="submit"
            className="w-fit rounded bg-emerald-600 px-4 py-2 text-white disabled:opacity-50"
            disabled={!token || !session || isSending}
          >
            {isSending ? "Sending..." : "Send Turn"}
          </button>
        </form>
      </section>

      <section className="grid gap-3 rounded border p-4">
        <h2 className="text-xl font-semibold">Transcript + AI Feedback</h2>
        {turns.length === 0 ? (
          <p className="text-sm text-gray-600">No turns yet.</p>
        ) : (
          turns.map((turn, index) => (
            <article key={`${turn.transcript}-${index}`} className="rounded border p-3">
              <p className="font-medium">Learner: {turn.transcript}</p>
              <p className="mt-2">Tutor: {turn.assistant_response}</p>
              <p className="mt-1 text-xs text-gray-500">Latency: {turn.response_ms} ms</p>
            </article>
          ))
        )}
      </section>

      <section className="grid gap-3 rounded border p-4">
        <h2 className="text-xl font-semibold">Progress Snapshot (MVP)</h2>
        <p>Total turns: {progress.turns}</p>
        <p>Average latency: {progress.avgLatencyMs} ms</p>
        <p className="text-xs text-gray-500">Recent realtime events: {events.join(" | ") || "none"}</p>
      </section>

      <section className="grid gap-3 rounded border p-4">
        <h2 className="text-xl font-semibold">Metrics Dashboard</h2>
        <p>Turns processed: {metrics.turn_total}</p>
        <p>Turn errors: {metrics.turn_error_total}</p>
        <p>Last E2E latency: {metrics.e2e_latency_ms_last} ms</p>
        <div className="mt-2 grid gap-2">
          <div className="h-4 w-full rounded bg-gray-100">
            <div
              className="h-4 rounded bg-emerald-500"
              style={{ width: `${Math.min(100, metrics.turn_total * 8)}%` }}
            />
          </div>
          <div className="h-4 w-full rounded bg-gray-100">
            <div
              className="h-4 rounded bg-red-500"
              style={{ width: `${Math.min(100, metrics.turn_error_total * 20)}%` }}
            />
          </div>
          <div className="h-4 w-full rounded bg-gray-100">
            <div
              className="h-4 rounded bg-blue-500"
              style={{ width: `${Math.min(100, metrics.e2e_latency_ms_last / 20)}%` }}
            />
          </div>
        </div>
      </section>
    </main>
  );
}
