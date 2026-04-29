"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { getProgress } from "@/lib/api";
import type { ProgressData } from "@/lib/types";
import Sidebar from "@/components/sidebar";

export default function ProgressPage() {
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const [learnerId, setLearnerId] = useState("student-demo");
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadProgress = useCallback(
    async (id: string) => {
      if (!token || !id.trim()) return;
      setLoading(true);
      setError("");
      try {
        const data = await getProgress(token, id);
        setProgress(data);
      } catch {
        setError("Khong the tai tien do hoc tap");
      } finally {
        setLoading(false);
      }
    },
    [token],
  );

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const data = await getProgress(token, learnerId);
        if (!cancelled) setProgress(data);
      } catch {
        if (!cancelled) setError("Khong the tai tien do hoc tap");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token, learnerId]);

  function handleSearch(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    loadProgress(learnerId);
  }

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="mx-auto max-w-4xl px-6 py-8">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Tien do hoc tap</h1>
            <p className="mt-1 text-sm text-gray-500">
              Theo doi tien trinh hoc tap cua hoc sinh
            </p>
          </div>

          <form onSubmit={handleSearch} className="mb-8 flex gap-3">
            <input
              value={learnerId}
              onChange={(e) => setLearnerId(e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
              placeholder="Nhap ma hoc sinh..."
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? "Dang tai..." : "Xem tien do"}
            </button>
          </form>

          {error && (
            <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-700">
              {error}
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
                          <p className="font-medium text-gray-900">
                            {s.lesson_topic}
                          </p>
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
                  <p className="text-gray-500">
                    Hoc sinh chua co phien hoc nao
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
