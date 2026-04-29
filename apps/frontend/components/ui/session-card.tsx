"use client";

import { useRouter } from "next/navigation";
import type { Session } from "@/lib/types";

type Props = {
  session: Session;
};

export default function SessionCard({ session }: Props) {
  const router = useRouter();

  return (
    <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4 transition-shadow hover:shadow-sm">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-3">
          <h3 className="truncate font-medium text-gray-900">
            {session.lesson_topic}
          </h3>
          <span
            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
              session.status === "active"
                ? "bg-emerald-100 text-emerald-700"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {session.status === "active" ? "Dang hoc" : "Da ket thuc"}
          </span>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Hoc sinh: {session.learner_id} &middot;{" "}
          {new Date(session.created_at).toLocaleString("vi-VN")}
        </p>
      </div>
      {session.status === "active" && (
        <button
          type="button"
          onClick={() => router.push(`/session?id=${session.session_id}`)}
          className="ml-4 rounded-lg bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100"
        >
          Tiep tuc
        </button>
      )}
    </div>
  );
}
