"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import { createClass, listClasses } from "@/lib/api";
import type { ClassSummary } from "@/lib/types";

export default function TeacherClassesPage() {
  const { token, isAuthenticated } = useRequireRole(["teacher", "admin"]);
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const load = async () => {
    if (!token) return;
    try {
      const data = await listClasses(token);
      setClasses(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the tai");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await listClasses(token);
        if (cancelled) return;
        setClasses(data);
        setError("");
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

  async function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token) return;
    setCreating(true);
    setError("");
    try {
      await createClass(token, { name, description });
      setName("");
      setDescription("");
      setShowCreate(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the tao");
    } finally {
      setCreating(false);
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lop cua toi</h1>
          <p className="mt-1 text-sm text-gray-500">
            Quan ly lop hoc va hoc sinh
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {showCreate ? "Dong" : "Tao lop moi"}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 space-y-3 rounded-xl border border-indigo-200 bg-indigo-50 p-6"
        >
          <div>
            <label htmlFor="class-name" className="mb-1 block text-sm font-medium text-gray-700">Ten lop</label>
            <input
              id="class-name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
              placeholder="VD: Toan lop 6A"
            />
          </div>
          <div>
            <label htmlFor="class-desc" className="mb-1 block text-sm font-medium text-gray-700">Mo ta</label>
            <textarea
              id="class-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={creating || !name.trim()}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {creating ? "Dang tao..." : "Tao lop"}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Dang tai...
        </div>
      ) : classes.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Ban chua tao lop nao
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {classes.map((c) => (
            <Link
              key={c.class_id}
              href={`/teacher/classes/${c.class_id}`}
              className="rounded-xl border border-gray-200 bg-white p-5 hover:border-indigo-300 hover:shadow-sm"
            >
              <p className="text-base font-semibold text-gray-900">{c.name}</p>
              {c.description && (
                <p className="mt-1 text-sm text-gray-600">{c.description}</p>
              )}
              <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                <span>{c.member_count} hoc sinh</span>
                <span>{new Date(c.created_at).toLocaleDateString("vi-VN")}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
