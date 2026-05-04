"use client";

import { useEffect, useState } from "react";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import { useAuth } from "@/lib/auth-context";
import {
  getStudentProfile,
  listLearningMemories,
  listSkillAssessments,
} from "@/lib/api";
import type { LearningMemory, SkillAssessment, StudentProfile } from "@/lib/types";

export default function StudentProfilePage() {
  const { token, isAuthenticated } = useRequireRole(["student"]);
  const { email } = useAuth();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [memories, setMemories] = useState<LearningMemory[]>([]);
  const [skills, setSkills] = useState<SkillAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || !email) return;
    let cancelled = false;
    (async () => {
      try {
        const [p, m, s] = await Promise.all([
          getStudentProfile(token, email),
          listLearningMemories(token, email),
          listSkillAssessments(token, email),
        ]);
        if (cancelled) return;
        setProfile(p);
        setMemories(m);
        setSkills(s);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Khong the tai");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token, email]);

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

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Ho so hoc tap</h1>

      {/* Profile Overview */}
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
        </div>
      )}

      {/* Skill Assessments */}
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

      {/* Learning History */}
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
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
