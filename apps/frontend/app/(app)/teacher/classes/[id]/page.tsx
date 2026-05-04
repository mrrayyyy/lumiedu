"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import {
  addClassMember,
  createClassAssignment,
  deleteClassAssignment,
  getClassDetail,
  removeClassMember,
} from "@/lib/api";
import type { ClassDetail } from "@/lib/types";

export default function ClassDetailPage() {
  const { token, isAuthenticated } = useRequireRole(["teacher", "admin"]);
  const params = useParams<{ id: string }>();
  const classId = params?.id ?? "";

  const [detail, setDetail] = useState<ClassDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [studentEmail, setStudentEmail] = useState("");
  const [topic, setTopic] = useState("");
  const [topicDesc, setTopicDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    if (!token || !classId) return;
    try {
      const data = await getClassDetail(token, classId);
      setDetail(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the tai chi tiet lop");
    } finally {
      setLoading(false);
    }
  }, [token, classId]);

  useEffect(() => {
    if (!token || !classId) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await getClassDetail(token, classId);
        if (cancelled) return;
        setDetail(data);
        setError("");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Khong the tai chi tiet lop");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, classId]);

  async function handleAddMember(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token || !studentEmail.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await addClassMember(token, classId, studentEmail.trim());
      setStudentEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the them hoc sinh");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemoveMember(email: string) {
    if (!token) return;
    if (!confirm(`Xoa hoc sinh ${email} khoi lop?`)) return;
    try {
      await removeClassMember(token, classId, email);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the xoa");
    }
  }

  async function handleCreateAssignment(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token || !topic.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await createClassAssignment(token, classId, {
        lesson_topic: topic,
        description: topicDesc,
      });
      setTopic("");
      setTopicDesc("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the giao bai");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteAssignment(assignmentId: string) {
    if (!token) return;
    if (!confirm("Xoa bai giao nay?")) return;
    try {
      await deleteClassAssignment(token, classId, assignmentId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the xoa");
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {loading && !detail ? (
        <p className="text-gray-500">Dang tai...</p>
      ) : detail ? (
        <>
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">{detail.name}</h1>
            {detail.description && (
              <p className="mt-1 text-sm text-gray-600">{detail.description}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Giao vien: {detail.teacher_name || detail.teacher_email}
            </p>
          </div>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section className="rounded-xl border border-gray-200 bg-white p-5">
              <h2 className="mb-3 text-lg font-semibold text-gray-900">
                Hoc sinh ({detail.members.length})
              </h2>
              <form onSubmit={handleAddMember} className="mb-4 flex gap-2">
                <input
                  value={studentEmail}
                  onChange={(e) => setStudentEmail(e.target.value)}
                  placeholder="email hoc sinh@..."
                  className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={submitting || !studentEmail.trim()}
                  className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  Them
                </button>
              </form>
              {detail.members.length === 0 ? (
                <p className="text-sm text-gray-500">Chua co hoc sinh nao</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {detail.members.map((m) => (
                    <li
                      key={m.email}
                      className="flex items-center justify-between py-2"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {m.full_name || m.email}
                        </p>
                        <p className="text-xs text-gray-500">{m.email}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveMember(m.email)}
                        className="text-xs text-red-600 hover:text-red-800"
                      >
                        Xoa
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="rounded-xl border border-gray-200 bg-white p-5">
              <h2 className="mb-3 text-lg font-semibold text-gray-900">
                Bai giao ({detail.assignments.length})
              </h2>
              <form onSubmit={handleCreateAssignment} className="mb-4 space-y-2">
                <input
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Chu de bai hoc"
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
                />
                <textarea
                  value={topicDesc}
                  onChange={(e) => setTopicDesc(e.target.value)}
                  placeholder="Mo ta (tuy chon)"
                  rows={2}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={submitting || !topic.trim()}
                  className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  Giao bai
                </button>
              </form>
              {detail.assignments.length === 0 ? (
                <p className="text-sm text-gray-500">Chua co bai giao nao</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {detail.assignments.map((a) => (
                    <li
                      key={a.assignment_id}
                      className="flex items-start justify-between py-2"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {a.lesson_topic}
                        </p>
                        {a.description && (
                          <p className="text-xs text-gray-600">{a.description}</p>
                        )}
                        <p className="text-xs text-gray-400">
                          {new Date(a.created_at).toLocaleDateString("vi-VN")}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteAssignment(a.assignment_id)}
                        className="text-xs text-red-600 hover:text-red-800"
                      >
                        Xoa
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      ) : (
        <p className="text-gray-500">Khong tim thay lop hoc.</p>
      )}
    </div>
  );
}
