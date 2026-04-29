"use client";

import Link from "next/link";
import { ChevronLeftIcon } from "@/components/icons";

type WsStatus = "connecting" | "connected" | "disconnected";

type Props = {
  topic: string;
  learnerId: string;
  wsStatus: WsStatus;
  onEnd: () => void;
};

export default function SessionHeader({ topic, learnerId, wsStatus, onEnd }: Props) {
  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <div className="flex items-center gap-4">
        <Link
          href="/dashboard"
          className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <ChevronLeftIcon />
        </Link>
        <div>
          <h1 className="font-semibold text-gray-900">{topic}</h1>
          <p className="text-xs text-gray-500">Hoc sinh: {learnerId}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span
          className={`flex items-center gap-1.5 text-xs ${
            wsStatus === "connected" ? "text-emerald-600" : "text-gray-400"
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              wsStatus === "connected" ? "bg-emerald-500" : "bg-gray-300"
            }`}
          />
          {wsStatus === "connected" ? "Ket noi" : "Ngat ket noi"}
        </span>
        <button
          type="button"
          onClick={onEnd}
          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
        >
          Ket thuc
        </button>
      </div>
    </header>
  );
}
