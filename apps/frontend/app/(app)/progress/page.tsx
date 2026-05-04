"use client";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useRequireAuth } from "@/lib/hooks/use-require-auth";
import {
  getProgress,
  listMyChildren,
  listTeacherStudents,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { ProgressData, UserSummary } from "@/lib/types";
import ErrorAlert from "@/components/ui/error-alert";

function ProgressContent() {
  const { token, isAuthenticated } = useRequireAuth();
  const { role, email } = useAuth();
  const searchParams = useSearchParams();
  const initialLearner = searchParams.get("learner") ?? "";

  const [learnerOptions, setLearnerOptions] = useState<UserSummary[]>([]);
  const [learnerId, setLearnerId] = useState("");
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isLocked = role === "student";
  const useDropdown = role === "teacher" || role === "parent";

  const effectiveLearner = useMemo(() => {
    if (role === "student") return email;
    return learnerId.trim();
  }, [role, email, learnerId]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      if (role === "teacher") {
        const data = await listTeacherStudents(token);
        if (cancelled) return;
        setLearnerOptions(data);
        if (!learnerId) {
          if (initialLearner) setLearnerId(initialLearner);
          else if (data.length > 0) setLearnerId(data[0].email);
        }
        return;
      }
      if (role === "parent") {
        const data = await listMyChildren(token);
        if (cancelled) return;
        setLearnerOptions(data);
        if (!learnerId) {
          if (initialLearner) setLearnerId(initialLearner);
          else if (data.length > 0) setLearnerId(data[0].email);
        }
        return;
      }
      await Promise.resolve();
      if (cancelled) return;
      if (role === "student") {
        setLearnerId(email);
      } else if (role === "admin" && !learnerId) {
        setLearnerId(initialLearner || email || "");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, role, email, initialLearner, learnerId]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      if (!effectiveLearner) {
        await Promise.resolve();
        if (!cancelled) setProgress(null);
        return;
      }
      setLoading(true);
      setError("");
      try {
        const data = await getProgress(token, effectiveLearner);
        if (!cancelled) setProgress(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Khong the tai tien do hoc tap");
          setProgress(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, effectiveLearner]);

  async function handleSearch(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token || !effectiveLearner) return;
    setLoading(true);
    setError("");
    try {
      const data = await getProgress(token, effectiveLearner);
      setProgress(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the tai tien do hoc tap");
      setProgress(null);
    } finally {
      setLoading(false);
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Tien do hoc tap</h1>
        <p className="mt-1 text-sm text-gray-500">
          Theo doi tien trinh hoc tap cua hoc sinh
        </p>
      </div>

      {!isLocked && (
        <form onSubmit={handleSearch} className="mb-8 flex gap-3">
          {useDropdown ? (
            <select
              value={learnerId}
              onChange={(e) => setLearnerId(e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
            >
              <option value="">-- Chon hoc sinh --</option>
              {learnerOptions.map((s) => (
                <option key={s.email} value={s.email}>
                  {s.full_name || s.email} ({s.email})
                </option>
              ))}
            </select>
          ) : (
            <input
              value={learnerId}
              onChange={(e) => setLearnerId(e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
              placeholder="Nhap ma hoc sinh..."
            />
          )}
          <button
            type="submit"
            disabled={loading || !effectiveLearner}
            className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Dang tai..." : "Xem tien do"}
          </button>
        </form>
      )}

      {isLocked && (
        <div className="mb-6 rounded-lg border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-900">
          Tien do cua ban: <span className="font-medium">{email}</span>
        </div>
      )}

      {error && (
        <div className="mb-6">
          <ErrorAlert message={error} />
        </div>
      )}

      {progress && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <p className="text-sm text-gray-500">Tong phien hoc</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {progress.total_sessions}
              </p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <p className="text-sm text-gray-500">Tong luot hoi dap</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {progress.total_turns}
              </p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <p className="text-sm text-gray-500">Chu de da hoc</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {progress.topics_studied.length}
              </p>
            </div>
          </div>

          {progress.topics_studied.length > 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <h3 className="mb-3 font-semibold text-gray-900">Cac chu de da hoc</h3>
              <div className="flex flex-wrap gap-2">
                {progress.topics_studied.map((topic) => (
                  <span
                    key={topic}
                    className="rounded-full bg-indigo-50 px-3 py-1 text-sm text-indigo-700"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {progress.recent_sessions.length > 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <h3 className="mb-4 font-semibold text-gray-900">
                Phien hoc gan day
              </h3>
              <div className="space-y-3">
                {progress.recent_sessions.map((s) => (
                  <div
                    key={s.session_id}
                    className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 p-4"
                  >
                    <div>
                      <p className="font-medium text-gray-900">{s.lesson_topic}</p>
                      <p className="mt-0.5 text-xs text-gray-500">
                        {new Date(s.created_at).toLocaleString("vi-VN")}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        s.status === "active"
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-gray-200 text-gray-600"
                      }`}
                    >
                      {s.status === "active" ? "Dang hoc" : "Hoan thanh"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {progress.total_sessions === 0 && (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center">
              <p className="text-gray-500">Hoc sinh chua co phien hoc nao</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ProgressPage() {
  return (
    <Suspense fallback={<div className="p-8 text-gray-500">Dang tai...</div>}>
      <ProgressContent />
    </Suspense>
  );
}
