"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireAuth } from "@/lib/hooks/use-require-auth";
import { usePoll } from "@/lib/hooks/use-poll";
import { createSession, getMetrics, listSessions } from "@/lib/api";
import type { Metrics, Session } from "@/lib/types";
import { BoltIcon, ChatIcon, PlusIcon, WarningIcon, BookIcon } from "@/components/icons";
import StatCard from "@/components/ui/stat-card";
import SessionCard from "@/components/ui/session-card";

const TOPICS = [
  "Phan so lop 6",
  "So thap phan",
  "So nguyen",
  "Hinh hoc co ban",
  "Phep tinh co ban",
  "Ti so va ti le thuc",
];

export default function DashboardPage() {
  const router = useRouter();
  const { token, isAuthenticated } = useRequireAuth();
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

  usePoll(
    async () => {
      const m = await getMetrics(token);
      setMetrics(m);
    },
    5000,
    isAuthenticated,
  );

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

  if (!isAuthenticated) return null;

  return (
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
          <PlusIcon className="h-4 w-4" />
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
        <StatCard
          icon={<ChatIcon className="h-5 w-5 text-emerald-600" />}
          iconBg="bg-emerald-100"
          label="Tong luot hoi dap"
          value={metrics.turn_total}
        />
        <StatCard
          icon={<BoltIcon className="h-5 w-5 text-blue-600" />}
          iconBg="bg-blue-100"
          label="Do tre gan nhat"
          value={`${metrics.e2e_latency_ms_last} ms`}
        />
        <StatCard
          icon={<WarningIcon className="h-5 w-5 text-red-600" />}
          iconBg="bg-red-100"
          label="Loi pipeline"
          value={metrics.turn_error_total}
        />
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
            <BookIcon className="mx-auto h-12 w-12 text-gray-300" />
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
              <SessionCard key={s.session_id} session={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
