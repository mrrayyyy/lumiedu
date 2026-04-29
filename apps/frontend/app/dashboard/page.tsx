"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { createSession, getMetrics, listSessions } from "@/lib/api";
import type { Metrics, Session } from "@/lib/types";
import Sidebar from "@/components/sidebar";

export default function DashboardPage() {
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({
    turn_total: 0,
    turn_error_total: 0,
    e2e_latency_ms_last: 0,
  });
  const [learnerId, setLearnerId] = useState("student-demo");
  const [lessonTopic, setLessonTopic] = useState("");
  const [creating, setCreating] = useState(false);
  const [showNewSession, setShowNewSession] = useState(false);

  const loadData = useCallback(async () => {
    if (!token) return;
    const [sessionData, metricsData] = await Promise.all([
      listSessions(token),
      getMetrics(token),
    ]);
    setSessions(sessionData.sessions);
    setMetrics(metricsData);
  }, [token]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      const [sessionData, metricsData] = await Promise.all([
        listSessions(token),
        getMetrics(token),
      ]);
      if (!cancelled) {
        setSessions(sessionData.sessions);
        setMetrics(metricsData);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  useEffect(() => {
    if (!token) return;
    const interval = setInterval(async () => {
      const m = await getMetrics(token);
      setMetrics(m);
    }, 5000);
    return () => clearInterval(interval);
  }, [token]);

  async function handleCreateSession(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!learnerId.trim() || !lessonTopic.trim()) return;
    setCreating(true);
    try {
      const session = await createSession(token, learnerId, lessonTopic);
      router.push(`/session?id=${session.session_id}`);
    } catch {
      setCreating(false);
    }
  }

  const TOPICS = [
    "Phan so lop 6",
    "So thap phan",
    "So nguyen",
    "Hinh hoc co ban",
    "Phep tinh co ban",
    "Ti so va ti le thuc",
  ];

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Trang chu</h1>
              <p className="mt-1 text-sm text-gray-500">
                Quan ly phien hoc va theo doi tien do
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowNewSession(!showNewSession)}
              className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:from-indigo-700 hover:to-purple-700"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Phien hoc moi
            </button>
          </div>

          {showNewSession && (
            <div className="mb-6 rounded-xl border border-indigo-200 bg-indigo-50 p-6">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                Tao phien hoc moi
              </h2>
              <form onSubmit={handleCreateSession} className="space-y-4">
                <div>
                  <label htmlFor="learner-id" className="mb-1.5 block text-sm font-medium text-gray-700">
                    Ma hoc sinh
                  </label>
                  <input
                    id="learner-id"
                    value={learnerId}
                    onChange={(e) => setLearnerId(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
                    placeholder="VD: student-001"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="topic" className="mb-1.5 block text-sm font-medium text-gray-700">
                    Chu de bai hoc
                  </label>
                  <input
                    id="topic"
                    value={lessonTopic}
                    onChange={(e) => setLessonTopic(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
                    placeholder="VD: Phan so lop 6"
                    required
                  />
                  <div className="mt-2 flex flex-wrap gap-2">
                    {TOPICS.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setLessonTopic(t)}
                        className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                          lessonTopic === t
                            ? "border-indigo-500 bg-indigo-100 text-indigo-700"
                            : "border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={creating || !learnerId.trim() || !lessonTopic.trim()}
                    className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {creating ? "Dang tao..." : "Bat dau hoc"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowNewSession(false)}
                    className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50"
                  >
                    Huy
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100">
                  <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Tong luot hoi dap</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.turn_total}</p>
                </div>
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                  <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Do tre gan nhat</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.e2e_latency_ms_last} ms</p>
                </div>
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100">
                  <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Loi pipeline</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.turn_error_total}</p>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Phien hoc gan day</h2>
              <button
                type="button"
                onClick={loadData}
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                Lam moi
              </button>
            </div>

            {sessions.length === 0 ? (
              <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <p className="mt-4 text-sm text-gray-500">Chua co phien hoc nao</p>
                <button
                  type="button"
                  onClick={() => setShowNewSession(true)}
                  className="mt-3 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                >
                  Tao phien hoc dau tien
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((s) => (
                  <div
                    key={s.session_id}
                    className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4 transition-shadow hover:shadow-sm"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="truncate font-medium text-gray-900">
                          {s.lesson_topic}
                        </h3>
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            s.status === "active"
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {s.status === "active" ? "Dang hoc" : "Da ket thuc"}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-500">
                        Hoc sinh: {s.learner_id} &middot;{" "}
                        {new Date(s.created_at).toLocaleString("vi-VN")}
                      </p>
                    </div>
                    {s.status === "active" && (
                      <button
                        type="button"
                        onClick={() => router.push(`/session?id=${s.session_id}`)}
                        className="ml-4 rounded-lg bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100"
                      >
                        Tiep tuc
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
