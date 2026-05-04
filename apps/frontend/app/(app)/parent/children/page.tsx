"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import { listMyChildren } from "@/lib/api";
import type { UserSummary } from "@/lib/types";

export default function ParentChildrenPage() {
  const { token, isAuthenticated } = useRequireRole(["parent"]);
  const [children, setChildren] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await listMyChildren(token);
        if (!cancelled) setChildren(data);
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
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Cac con cua toi</h1>
        <p className="mt-1 text-sm text-gray-500">
          Theo doi qua trinh hoc tap cua con
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <p className="text-gray-500">Dang tai...</p>
      ) : children.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Chua co lien ket. Hay yeu cau quan tri vien lien ket tai khoan con cua ban.
        </div>
      ) : (
        <div className="space-y-3">
          {children.map((c) => (
            <div
              key={c.email}
              className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-5"
            >
              <div>
                <p className="text-base font-semibold text-gray-900">
                  {c.full_name || c.email}
                </p>
                <p className="text-xs text-gray-500">{c.email}</p>
                {c.grade_level && (
                  <p className="mt-1 text-xs text-gray-500">Khoi: {c.grade_level}</p>
                )}
              </div>
              <Link
                href={`/progress?learner=${encodeURIComponent(c.email)}`}
                className="rounded-lg border border-indigo-300 bg-white px-3 py-1.5 text-sm text-indigo-700 hover:bg-indigo-50"
              >
                Xem tien do
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
