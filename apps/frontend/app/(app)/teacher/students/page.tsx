"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import { listTeacherStudents } from "@/lib/api";
import type { UserSummary } from "@/lib/types";

export default function TeacherStudentsPage() {
  const { token, isAuthenticated } = useRequireRole(["teacher", "admin"]);
  const [students, setStudents] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await listTeacherStudents(token);
        if (!cancelled) setStudents(data);
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

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Hoc sinh cua toi</h1>
        <p className="mt-1 text-sm text-gray-500">
          Tat ca hoc sinh trong cac lop cua ban
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <p className="text-gray-500">Dang tai...</p>
      ) : students.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Chua co hoc sinh nao trong lop cua ban
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Ho ten</th>
                <th className="px-4 py-3">Khoi/Lop</th>
                <th className="px-4 py-3 text-right" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {students.map((s) => (
                <tr key={s.email}>
                  <td className="px-4 py-3 font-medium text-gray-900">{s.email}</td>
                  <td className="px-4 py-3 text-gray-700">{s.full_name || "-"}</td>
                  <td className="px-4 py-3 text-gray-700">{s.grade_level || "-"}</td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/progress?learner=${encodeURIComponent(s.email)}`}
                      className="text-xs text-indigo-600 hover:text-indigo-800"
                    >
                      Xem tien do
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
