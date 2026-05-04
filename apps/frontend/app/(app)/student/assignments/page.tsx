"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import { createSession, listMyAssignments } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Assignment } from "@/lib/types";

export default function StudentAssignmentsPage() {
  const router = useRouter();
  const { token, isAuthenticated } = useRequireRole(["student"]);
  const { email } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState<string>("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await listMyAssignments(token);
        if (!cancelled) setAssignments(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Khong the tai");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleStart(a: Assignment) {
    if (!token) return;
    setStarting(a.assignment_id);
    setError("");
    try {
      const session = await createSession(token, email, a.lesson_topic);
      router.push(`/session?id=${session.session_id}`);
    } catch (err) {
      setStarting("");
      setError(err instanceof Error ? err.message : "Khong the bat dau");
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Bai duoc giao</h1>
        <p className="mt-1 text-sm text-gray-500">
          Cac bai hoc giao vien giao cho ban
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <p className="text-gray-500">Dang tai...</p>
      ) : assignments.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Hien chua co bai giao nao
        </div>
      ) : (
        <div className="space-y-3">
          {assignments.map((a) => (
            <div
              key={a.assignment_id}
              className="rounded-xl border border-gray-200 bg-white p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-base font-semibold text-gray-900">{a.lesson_topic}</p>
                  {a.class_name && (
                    <p className="text-xs text-gray-500">Lop: {a.class_name}</p>
                  )}
                  {a.description && (
                    <p className="mt-1 text-sm text-gray-600">{a.description}</p>
                  )}
                  {a.due_at && (
                    <p className="mt-1 text-xs text-amber-700">
                      Han: {new Date(a.due_at).toLocaleString("vi-VN")}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => handleStart(a)}
                  disabled={starting === a.assignment_id}
                  className="shrink-0 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {starting === a.assignment_id ? "Dang vao..." : "Hoc ngay"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
