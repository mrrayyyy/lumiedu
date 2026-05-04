"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import { deleteKnowledge, listKnowledge, uploadKnowledge } from "@/lib/api";
import type { KnowledgeDocument } from "@/lib/types";
import { BookIcon } from "@/components/icons";

const SUBJECTS = [
  { value: "math", label: "Toan" },
  { value: "physics", label: "Vat ly" },
  { value: "chemistry", label: "Hoa hoc" },
  { value: "biology", label: "Sinh hoc" },
  { value: "literature", label: "Ngu van" },
  { value: "english", label: "Tieng Anh" },
  { value: "other", label: "Khac" },
];

const GRADE_LEVELS = [
  { value: "grade6", label: "Lop 6" },
  { value: "grade7", label: "Lop 7" },
  { value: "grade8", label: "Lop 8" },
  { value: "grade9", label: "Lop 9" },
  { value: "grade10", label: "Lop 10" },
  { value: "grade11", label: "Lop 11" },
  { value: "grade12", label: "Lop 12" },
];

export default function TeacherKnowledgePage() {
  const { token, isAuthenticated } = useRequireRole(["teacher", "admin"]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("math");
  const [gradeLevel, setGradeLevel] = useState("grade6");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function loadDocs() {
    if (!token) return;
    try {
      const docs = await listKnowledge(token);
      setDocuments(docs);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the tai");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const docs = await listKnowledge(token);
        if (!cancelled) setDocuments(docs);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Khong the tai");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  async function handleUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token) return;
    const file = fileRef.current?.files?.[0];
    if (!file || !title.trim()) {
      setError("Vui long chon file va nhap tieu de");
      return;
    }
    setUploading(true);
    setError("");
    try {
      await uploadKnowledge(token, file, title, subject, gradeLevel);
      setTitle("");
      setShowUpload(false);
      if (fileRef.current) fileRef.current.value = "";
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload that bai");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(docId: string, docTitle: string) {
    if (!token) return;
    if (!window.confirm(`Ban co chac muon xoa tai lieu "${docTitle}"?`)) return;
    try {
      await deleteKnowledge(token, docId);
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xoa that bai");
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ngan kien thuc</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload tai lieu, bai giang de Agent su dung khi day hoc
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowUpload(!showUpload)}
          className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {showUpload ? "Dong" : "Upload tai lieu"}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {showUpload && (
        <form
          onSubmit={handleUpload}
          className="mb-6 space-y-3 rounded-xl border border-indigo-200 bg-indigo-50 p-6"
        >
          <div>
            <label htmlFor="doc-title" className="mb-1 block text-sm font-medium text-gray-700">
              Tieu de tai lieu
            </label>
            <input
              id="doc-title"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
              placeholder="VD: Bai giang Phan so lop 6"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="doc-subject" className="mb-1 block text-sm font-medium text-gray-700">
                Mon hoc
              </label>
              <select
                id="doc-subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
              >
                {SUBJECTS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="doc-grade" className="mb-1 block text-sm font-medium text-gray-700">
                Khoi lop
              </label>
              <select
                id="doc-grade"
                value={gradeLevel}
                onChange={(e) => setGradeLevel(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
              >
                {GRADE_LEVELS.map((g) => (
                  <option key={g.value} value={g.value}>{g.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label htmlFor="doc-file" className="mb-1 block text-sm font-medium text-gray-700">
              Chon file (PDF, DOCX, TXT, MD)
            </label>
            <input
              id="doc-file"
              type="file"
              ref={fileRef}
              accept=".pdf,.docx,.txt,.md"
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={uploading || !title.trim()}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {uploading ? "Dang upload..." : "Upload"}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Dang tai...
        </div>
      ) : documents.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Chua co tai lieu nao. Upload tai lieu de Agent co the su dung khi day hoc.
        </div>
      ) : (
        <div className="space-y-3">
          {documents.map((doc) => (
            <div
              key={doc.doc_id}
              className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100">
                  <BookIcon className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">{doc.title}</h3>
                  <p className="mt-0.5 text-xs text-gray-500">
                    {doc.original_filename} &middot; {doc.chunk_count} phan &middot;{" "}
                    {SUBJECTS.find((s) => s.value === doc.subject)?.label || doc.subject} &middot;{" "}
                    {GRADE_LEVELS.find((g) => g.value === doc.grade_level)?.label || doc.grade_level}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(doc.doc_id, doc.title)}
                className="rounded-lg px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
              >
                Xoa
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
