"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import {
  getStudentProfile,
  listLearningMemories,
  listSkillAssessments,
  updateStudentProfile,
} from "@/lib/api";
import type { LearningMemory, SkillAssessment, StudentProfile } from "@/lib/types";

export default function TeacherStudentProfilePage() {
  const { token, isAuthenticated } = useRequireRole(["teacher", "admin"]);
  const params = useParams<{ email: string }>();
  const studentEmail = decodeURIComponent(params?.email ?? "");

  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [memories, setMemories] = useState<LearningMemory[]>([]);
  const [skills, setSkills] = useState<SkillAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editNotes, setEditNotes] = useState(false);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!token || !studentEmail) return;
    let cancelled = false;
    (async () => {
      try {
        const [p, m, s] = await Promise.all([
          getStudentProfile(token, studentEmail),
          listLearningMemories(token, studentEmail),
          listSkillAssessments(token, studentEmail),
        ]);
        if (cancelled) return;
        setProfile(p);
        setNotes(p.notes || "");
        setMemories(m);
        setSkills(s);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Khong the tai");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token, studentEmail]);

  async function handleSaveNotes() {
    if (!token || !studentEmail) return;
    setSaving(true);
    try {
      const updated = await updateStudentProfile(token, studentEmail, { notes });
      setProfile(updated);
      setEditNotes(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Luu that bai");
    } finally {
      setSaving(false);
    }
  }

  if (!isAuthenticated) return null;

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Dang tai...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      </div>
    );
  }

  const difficultyLabel: Record<string, string> = {
    easy: "De",
    medium: "Trung binh",
    hard: "Kho",
  };
  const learningStyleLabel: Record<string, string> = {
    balanced: "Can bang",
    visual: "Truc quan",
    auditory: "Nghe",
    reading: "Doc",
    kinesthetic: "Thuc hanh",
  };

  const avgMastery = memories.length
    ? Math.round((memories.reduce((s, m) => s + m.mastery_score, 0) / memories.length) * 100)
    : 0;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link
            href="/teacher/students"
            className="text-xs text-indigo-600 hover:text-indigo-800"
          >
            &larr; Danh sach hoc sinh
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">{studentEmail}</h1>
          <p className="mt-0.5 text-sm text-gray-500">Ho so hoc tap</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-indigo-100 px-3 py-1.5 text-center">
            <p className="text-lg font-bold text-indigo-700">{avgMastery}%</p>
            <p className="text-xs text-indigo-600">TB mastery</p>
          </div>
          <div className="rounded-lg bg-green-100 px-3 py-1.5 text-center">
            <p className="text-lg font-bold text-green-700">{memories.length}</p>
            <p className="text-xs text-green-600">Buoi hoc</p>
          </div>
        </div>
      </div>

      {/* Profile */}
      {profile && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="text-lg font-semibold text-gray-800">Thong tin chung</h2>
          <div className="mt-3 grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs text-gray-500">Phong cach hoc</span>
              <p className="text-sm font-medium text-gray-900">
                {learningStyleLabel[profile.learning_style] || profile.learning_style}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Muc do kho</span>
              <p className="text-sm font-medium text-gray-900">
                {difficultyLabel[profile.difficulty_level] || profile.difficulty_level}
              </p>
            </div>
          </div>

          <div className="mt-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Ghi chu giao vien</span>
              <button
                type="button"
                onClick={() => setEditNotes(!editNotes)}
                className="text-xs text-indigo-600 hover:text-indigo-800"
              >
                {editNotes ? "Huy" : "Sua"}
              </button>
            </div>
            {editNotes ? (
              <div className="mt-1">
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  rows={3}
                />
                <button
                  type="button"
                  disabled={saving}
                  onClick={handleSaveNotes}
                  className="mt-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving ? "Dang luu..." : "Luu"}
                </button>
              </div>
            ) : (
              <p className="mt-1 text-sm text-gray-700">{profile.notes || "Chua co ghi chu"}</p>
            )}
          </div>
        </div>
      )}

      {/* Skills */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-gray-800">Ky nang</h2>
        {skills.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">Chua co du lieu ky nang</p>
        ) : (
          <div className="mt-3 space-y-2">
            {skills.map((s) => (
              <div key={s.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2">
                <div>
                  <span className="text-sm font-medium text-gray-800">{s.topic}</span>
                  <span className="ml-2 text-xs text-gray-500">{s.sub_skill}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">
                    {s.correct_count}/{s.total_attempts}
                  </span>
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full rounded-full bg-indigo-500"
                      style={{ width: `${Math.round(s.mastery_rate * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-700">
                    {Math.round(s.mastery_rate * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Learning Memories */}
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-gray-800">Lich su hoc tap</h2>
        {memories.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">Chua co buoi hoc nao duoc ghi nhan</p>
        ) : (
          <div className="mt-3 space-y-3">
            {memories.map((m) => (
              <div key={m.memory_id} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {new Date(m.created_at).toLocaleDateString("vi-VN")}
                  </span>
                  <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                    {Math.round(m.mastery_score * 100)}%
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-800">{m.summary}</p>
                {m.topics_covered && (
                  <p className="mt-1 text-xs text-gray-500">Chu de: {m.topics_covered}</p>
                )}
                {m.mistakes_made && (
                  <p className="mt-1 text-xs text-red-500">Loi: {m.mistakes_made}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
