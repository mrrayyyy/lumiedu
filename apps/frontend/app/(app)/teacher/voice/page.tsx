"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import {
  createVoiceProfile,
  deleteVoiceProfile,
  listVoiceProfiles,
  trainVoiceProfile,
  uploadVoiceSample,
} from "@/lib/api";
import type { VoiceProfile } from "@/lib/types";

const STATUS_LABELS: Record<string, string> = {
  pending: "Cho xu ly",
  training: "Dang training...",
  ready: "San sang",
  failed: "That bai",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  training: "bg-blue-100 text-blue-700",
  ready: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function TeacherVoicePage() {
  const { token, isAuthenticated } = useRequireRole(["teacher", "admin"]);
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [voiceName, setVoiceName] = useState("");
  const [creating, setCreating] = useState(false);
  const [uploadingId, setUploadingId] = useState("");
  const [trainingId, setTrainingId] = useState("");
  const audioRef = useRef<HTMLInputElement>(null);

  async function loadProfiles() {
    if (!token) return;
    try {
      const data = await listVoiceProfiles(token);
      setProfiles(data);
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
        const data = await listVoiceProfiles(token);
        if (!cancelled) setProfiles(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Khong the tai");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  async function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token || !voiceName.trim()) return;
    setCreating(true);
    setError("");
    try {
      await createVoiceProfile(token, voiceName);
      setVoiceName("");
      setShowCreate(false);
      await loadProfiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tao that bai");
    } finally {
      setCreating(false);
    }
  }

  async function handleUploadSample(profileId: string) {
    if (!token) return;
    const file = audioRef.current?.files?.[0];
    if (!file) {
      setError("Vui long chon file audio");
      return;
    }
    setUploadingId(profileId);
    setError("");
    try {
      await uploadVoiceSample(token, profileId, file);
      if (audioRef.current) audioRef.current.value = "";
      await loadProfiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload that bai");
    } finally {
      setUploadingId("");
    }
  }

  async function handleTrain(profileId: string) {
    if (!token) return;
    setTrainingId(profileId);
    setError("");
    try {
      await trainVoiceProfile(token, profileId);
      await loadProfiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Training that bai");
    } finally {
      setTrainingId("");
    }
  }

  async function handleDelete(profileId: string) {
    if (!token) return;
    try {
      await deleteVoiceProfile(token, profileId);
      await loadProfiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xoa that bai");
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Voice Studio</h1>
          <p className="mt-1 text-sm text-gray-500">
            Tao va quan ly giong noi AI giong giao vien
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {showCreate ? "Dong" : "Tao voice moi"}
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
            <label htmlFor="voice-name" className="mb-1 block text-sm font-medium text-gray-700">
              Ten giong noi
            </label>
            <input
              id="voice-name"
              required
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
              placeholder="VD: Giong co Lan"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={creating || !voiceName.trim()}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {creating ? "Dang tao..." : "Tao voice"}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Dang tai...
        </div>
      ) : profiles.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white py-12 text-center text-sm text-gray-500">
          Chua co voice profile nao. Tao giong noi moi de hoc sinh nghe giong giao vien.
        </div>
      ) : (
        <div className="space-y-4">
          {profiles.map((p) => (
            <div
              key={p.profile_id}
              className="rounded-xl border border-gray-200 bg-white p-5"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{p.voice_name}</h3>
                  <p className="mt-0.5 text-xs text-gray-500">
                    {p.sample_count} mau audio &middot; Provider: {p.provider}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[p.status] || "bg-gray-100 text-gray-700"}`}>
                    {STATUS_LABELS[p.status] || p.status}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDelete(p.profile_id)}
                    className="rounded-lg px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                  >
                    Xoa
                  </button>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-3">
                <input
                  type="file"
                  ref={audioRef}
                  accept=".mp3,.wav,.ogg,.m4a,.webm"
                  className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs"
                />
                <button
                  type="button"
                  disabled={uploadingId === p.profile_id}
                  onClick={() => handleUploadSample(p.profile_id)}
                  className="rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                >
                  {uploadingId === p.profile_id ? "Uploading..." : "Upload mau"}
                </button>
                {p.sample_count > 0 && p.status !== "ready" && (
                  <button
                    type="button"
                    disabled={trainingId === p.profile_id}
                    onClick={() => handleTrain(p.profile_id)}
                    className="rounded-lg bg-indigo-100 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-200 disabled:opacity-50"
                  >
                    {trainingId === p.profile_id ? "Training..." : "Bat dau training"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="text-sm font-semibold text-blue-900">Huong dan tao giong noi</h3>
        <ol className="mt-2 list-inside list-decimal space-y-1 text-xs text-blue-800">
          <li>Tao voice profile moi voi ten giong noi</li>
          <li>Upload it nhat 1 file audio (doc bai mau, 3-10 phut)</li>
          <li>Nhan &ldquo;Bat dau training&rdquo; de he thong hoc giong noi</li>
          <li>Khi trang thai &ldquo;San sang&rdquo;, gan voice vao lop hoc</li>
        </ol>
      </div>
    </div>
  );
}
