"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireAuth } from "@/lib/hooks/use-require-auth";
import { usePoll } from "@/lib/hooks/use-poll";
import {
  createSession,
  getMetrics,
  listClasses,
  listMyChildren,
  listSessions,
  listTeacherStudents,
} from "@/lib/api";
import { useAuth, ROLE_LABELS } from "@/lib/auth-context";
import type {
  ClassSummary,
  Metrics,
  Session,
  UserSummary,
} from "@/lib/types";
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
  const { role, email, fullName } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({
    turn_total: 0,
    turn_error_total: 0,
    e2e_latency_ms_last: 0,
  });
  const [learnerId, setLearnerId] = useState("");
  const [lessonTopic, setLessonTopic] = useState("");
  const [creating, setCreating] = useState(false);
  const [showNewSession, setShowNewSession] = useState(false);
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [teacherStudents, setTeacherStudents] = useState<UserSummary[]>([]);
  const [parentChildren, setParentChildren] = useState<UserSummary[]>([]);
  const [errorMsg, setErrorMsg] = useState("");

  const canStartSession = role === "admin" || role === "teacher" || role === "student";

  async function loadData() {
    if (!token) return;
    if (role === "student") {
      const sessionData = await listSessions(token, email);
      setSessions(sessionData.sessions);
    } else if (role === "admin") {
      const sessionData = await listSessions(token);
      setSessions(sessionData.sessions);
    }
    const metricsData = await getMetrics(token);
    setMetrics(metricsData);
  }

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      const tasks: Promise<unknown>[] = [];
      tasks.push(getMetrics(token).then((m) => !cancelled && setMetrics(m)));
      if (role === "student") {
        tasks.push(
          listSessions(token, email).then((d) => !cancelled && setSessions(d.sessions)),
        );
        setLearnerId(email);
      } else if (role === "admin") {
        tasks.push(
          listSessions(token).then((d) => !cancelled && setSessions(d.sessions)),
        );
      } else if (role === "teacher") {
        tasks.push(
          listClasses(token).then((d) => !cancelled && setClasses(d)),
        );
        tasks.push(
          listTeacherStudents(token).then((d) => !cancelled && setTeacherStudents(d)),
        );
      } else if (role === "parent") {
        tasks.push(
          listMyChildren(token).then((d) => !cancelled && setParentChildren(d)),
        );
      }
      await Promise.all(tasks);
    })();
    return () => {
      cancelled = true;
    };
  }, [token, role, email]);

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
    setErrorMsg("");
    const targetLearner = role === "student" ? email : learnerId.trim();
    if (!targetLearner || !lessonTopic.trim()) {
      setErrorMsg("Vui long chon hoc sinh va chu de");
      return;
    }
    setCreating(true);
    try {
      const session = await createSession(token, targetLearner, lessonTopic);
      router.push(`/session?id=${session.session_id}`);
    } catch (err) {
      setCreating(false);
      setErrorMsg(err instanceof Error ? err.message : "Khong the tao phien hoc");
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Xin chao{fullName ? `, ${fullName}` : ""}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {ROLE_LABELS[role]} - {email}
          </p>
        </div>
        {canStartSession && (
          <button
            type="button"
            onClick={() => setShowNewSession(!showNewSession)}
            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:from-indigo-700 hover:to-purple-700"
          >
            <PlusIcon className="h-4 w-4" />
            Phien hoc moi
          </button>
        )}
      </div>

      {showNewSession && canStartSession && (
        <div className="mb-6 rounded-xl border border-indigo-200 bg-indigo-50 p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Tao phien hoc moi
          </h2>
          {errorMsg && (
            <div className="mb-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {errorMsg}
            </div>
          )}
          <form onSubmit={handleCreateSession} className="space-y-4">
            {role === "student" && (
              <div className="text-sm text-gray-700">
                Hoc sinh: <span className="font-medium">{email}</span>
              </div>
            )}
            {role === "admin" && (
              <div>
                <label htmlFor="learner-id" className="mb-1.5 block text-sm font-medium text-gray-700">
                  Ma hoc sinh
                </label>
                <input
                  id="learner-id"
                  value={learnerId}
                  onChange={(e) => setLearnerId(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
                  placeholder="email hoac ma dinh danh"
                  required
                />
              </div>
            )}
            {role === "teacher" && (
              <div>
                <label htmlFor="learner-select" className="mb-1.5 block text-sm font-medium text-gray-700">
                  Hoc sinh
                </label>
                <select
                  id="learner-select"
                  value={learnerId}
                  onChange={(e) => setLearnerId(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
                  required
                >
                  <option value="">-- Chon hoc sinh --</option>
                  {teacherStudents.map((s) => (
                    <option key={s.email} value={s.email}>
                      {s.full_name || s.email} ({s.email})
                    </option>
                  ))}
                </select>
                {teacherStudents.length === 0 && (
                  <p className="mt-2 text-xs text-amber-700">
                    Ban chua co hoc sinh nao trong lop. Hay tao lop va them hoc sinh truoc.
                  </p>
                )}
              </div>
            )}
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
                disabled={creating || !lessonTopic.trim()}
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

      {role !== "parent" && (
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
      )}

      {role === "teacher" && (
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            icon={<BookIcon className="h-5 w-5 text-indigo-600" strokeWidth={2} />}
            iconBg="bg-indigo-100"
            label="Lop hoc"
            value={classes.length}
          />
          <StatCard
            icon={<HomeStudentIcon />}
            iconBg="bg-emerald-100"
            label="Hoc sinh"
            value={teacherStudents.length}
          />
          <div />
        </div>
      )}

      {role === "parent" && (
        <div className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Cac con cua ban</h2>
          </div>
          {parentChildren.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center">
              <p className="text-sm text-gray-500">
                Chua co lien ket. Hay yeu cau quan tri vien lien ket tai khoan con cua ban.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {parentChildren.map((c) => (
                <div
                  key={c.email}
                  className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {c.full_name || c.email}
                    </p>
                    <p className="text-xs text-gray-500">{c.email}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => router.push(`/progress?learner=${encodeURIComponent(c.email)}`)}
                    className="rounded-lg border border-indigo-300 bg-white px-3 py-1.5 text-sm text-indigo-700 hover:bg-indigo-50"
                  >
                    Xem tien do
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {role !== "parent" && role !== "teacher" && (
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
              {canStartSession && (
                <button
                  type="button"
                  onClick={() => setShowNewSession(true)}
                  className="mt-3 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                >
                  Tao phien hoc dau tien
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {sessions.map((s) => (
                <SessionCard key={s.session_id} session={s} />
              ))}
            </div>
          )}
        </div>
      )}

      {role === "teacher" && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Lop cua toi</h2>
            <button
              type="button"
              onClick={() => router.push("/teacher/classes")}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Quan ly lop
            </button>
          </div>
          {classes.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center">
              <p className="text-sm text-gray-500">Ban chua tao lop nao</p>
              <button
                type="button"
                onClick={() => router.push("/teacher/classes")}
                className="mt-3 text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                Tao lop dau tien
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {classes.map((c) => (
                <button
                  type="button"
                  key={c.class_id}
                  onClick={() => router.push(`/teacher/classes/${c.class_id}`)}
                  className="flex w-full items-center justify-between rounded-lg border border-gray-200 bg-white p-4 text-left hover:border-indigo-300 hover:bg-indigo-50"
                >
                  <div>
                    <p className="font-medium text-gray-900">{c.name}</p>
                    <p className="text-xs text-gray-500">
                      {c.member_count} hoc sinh
                    </p>
                  </div>
                  <span className="text-xs text-indigo-700">Chi tiet &rarr;</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function HomeStudentIcon() {
  return (
    <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l9-5-9-5-9 5 9 5z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
    </svg>
  );
}
