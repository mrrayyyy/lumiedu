import type {
  Metrics,
  ProgressData,
  Session,
  SessionListResponse,
  TokenResponse,
  Turn,
  TurnHistoryItem,
} from "./types";

const API_BASE = "/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function authHeaders(token: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(
      (data as Record<string, string>).detail || "Dang nhap that bai",
      res.status,
    );
  }
  return (await res.json()) as TokenResponse;
}

export async function createSession(
  token: string,
  learnerId: string,
  lessonTopic: string,
): Promise<Session> {
  const res = await fetch(`${API_BASE}/v1/sessions`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ learner_id: learnerId, lesson_topic: lessonTopic }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(
      (data as Record<string, string>).detail || "Khong the tao phien hoc",
      res.status,
    );
  }
  return (await res.json()) as Session;
}

export async function listSessions(
  token: string,
  learnerId?: string,
): Promise<SessionListResponse> {
  const params = learnerId ? `?learner_id=${encodeURIComponent(learnerId)}` : "";
  const res = await fetch(`${API_BASE}/v1/sessions${params}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    return { sessions: [], total: 0 };
  }
  return (await res.json()) as SessionListResponse;
}

export async function getSession(token: string, sessionId: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/v1/sessions/${sessionId}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw new ApiError("Phien hoc khong ton tai", res.status);
  }
  return (await res.json()) as Session;
}

export async function endSession(
  token: string,
  sessionId: string,
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/v1/sessions/${sessionId}/end`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw new ApiError("Khong the ket thuc phien hoc", res.status);
  }
  return (await res.json()) as { status: string };
}

export async function submitTurn(
  token: string,
  sessionId: string,
  textInput: string,
  audioBase64?: string,
): Promise<Turn> {
  const body: Record<string, string> = { text_input: textInput };
  if (audioBase64) {
    body.audio_base64 = audioBase64;
  }
  const res = await fetch(`${API_BASE}/v1/sessions/${sessionId}/turns`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ApiError("Gui cau hoi that bai", res.status);
  }
  return (await res.json()) as Turn;
}

export async function getSessionTurns(
  token: string,
  sessionId: string,
): Promise<TurnHistoryItem[]> {
  const res = await fetch(`${API_BASE}/v1/sessions/${sessionId}/turns`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    return [];
  }
  return (await res.json()) as TurnHistoryItem[];
}

export async function getProgress(
  token: string,
  learnerId: string,
): Promise<ProgressData> {
  const res = await fetch(`${API_BASE}/v1/progress/${encodeURIComponent(learnerId)}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw new ApiError("Khong the tai tien do", res.status);
  }
  return (await res.json()) as ProgressData;
}

export async function getMetrics(token: string): Promise<Metrics> {
  const res = await fetch(`${API_BASE}/metrics`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    return { turn_total: 0, turn_error_total: 0, e2e_latency_ms_last: 0 };
  }
  return (await res.json()) as Metrics;
}

export { ApiError };
