"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import { listClasses } from "@/lib/api";
import type { ClassSummary } from "@/lib/types";

export default function AdminClassesPage() {
  const { token, isAuthenticated } = useRequireRole(["admin"]);
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await listClasses(token);
        if (!cancelled) setClasses(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Khong the tai");
        }
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
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tat ca lop hoc</h1>
        <p className="mt-1 text-sm text-gray-500">Toan bo lop hoc trong he thong</p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">Ten lop</th>
              <th className="px-4 py-3">Giao vien</th>
              <th className="px-4 py-3">So hoc sinh</th>
              <th className="px-4 py-3">Ngay tao</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">Dang tai...</td>
              </tr>
            )}
            {!loading && classes.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">Chua co lop hoc</td>
              </tr>
            )}
            {classes.map((c) => (
              <tr key={c.class_id}>
                <td className="px-4 py-3 font-medium text-gray-900">{c.name}</td>
                <td className="px-4 py-3 text-gray-700">
                  {c.teacher_name || c.teacher_email}
                  <p className="text-xs text-gray-400">{c.teacher_email}</p>
                </td>
                <td className="px-4 py-3 text-gray-700">{c.member_count}</td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(c.created_at).toLocaleDateString("vi-VN")}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/teacher/classes/${c.class_id}`}
                    className="text-xs text-indigo-600 hover:text-indigo-800"
                  >
                    Chi tiet
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
