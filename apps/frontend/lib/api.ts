import type {
  Assignment,
  AssignmentCreateInput,
  ClassCreateInput,
  ClassDetail,
  ClassSummary,
  KnowledgeDocument,
  LearningMemory,
  Metrics,
  ProgressData,
  Session,
  SessionListResponse,
  SkillAssessment,
  StudentProfile,
  TokenResponse,
  Turn,
  TurnHistoryItem,
  UserCreateInput,
  UserListResponse,
  UserSummary,
  UserUpdateInput,
  VoiceProfile,
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

async function parseError(res: Response, fallback: string): Promise<ApiError> {
  const data = await res.json().catch(() => ({}));
  return new ApiError(
    (data as Record<string, string>).detail || fallback,
    res.status,
  );
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    throw await parseError(res, "Dang nhap that bai");
  }
  return (await res.json()) as TokenResponse;
}

export async function getMe(token: string): Promise<UserSummary> {
  const res = await fetch(`${API_BASE}/v1/auth/me`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the lay thong tin tai khoan");
  }
  return (await res.json()) as UserSummary;
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
    throw await parseError(res, "Khong the tao phien hoc");
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
    throw await parseError(res, "Phien hoc khong ton tai");
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
    throw await parseError(res, "Khong the ket thuc phien hoc");
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
    throw await parseError(res, "Gui cau hoi that bai");
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
    throw await parseError(res, "Khong the tai tien do");
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

export async function listUsers(
  token: string,
  role?: string,
): Promise<UserListResponse> {
  const params = role ? `?role=${encodeURIComponent(role)}` : "";
  const res = await fetch(`${API_BASE}/v1/users${params}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai danh sach nguoi dung");
  }
  return (await res.json()) as UserListResponse;
}

export async function createUser(
  token: string,
  input: UserCreateInput,
): Promise<UserSummary> {
  const res = await fetch(`${API_BASE}/v1/users`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tao nguoi dung");
  }
  return (await res.json()) as UserSummary;
}

export async function updateUser(
  token: string,
  email: string,
  input: UserUpdateInput,
): Promise<UserSummary> {
  const res = await fetch(`${API_BASE}/v1/users/${encodeURIComponent(email)}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the cap nhat nguoi dung");
  }
  return (await res.json()) as UserSummary;
}

export async function deleteUser(token: string, email: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/users/${encodeURIComponent(email)}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the xoa nguoi dung");
  }
}

export async function listClasses(token: string): Promise<ClassSummary[]> {
  const res = await fetch(`${API_BASE}/v1/classes`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai danh sach lop");
  }
  return (await res.json()) as ClassSummary[];
}

export async function createClass(
  token: string,
  input: ClassCreateInput,
): Promise<ClassSummary> {
  const res = await fetch(`${API_BASE}/v1/classes`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tao lop hoc");
  }
  return (await res.json()) as ClassSummary;
}

export async function getClassDetail(token: string, classId: string): Promise<ClassDetail> {
  const res = await fetch(`${API_BASE}/v1/classes/${classId}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai chi tiet lop");
  }
  return (await res.json()) as ClassDetail;
}

export async function addClassMember(
  token: string,
  classId: string,
  studentEmail: string,
): Promise<UserSummary[]> {
  const res = await fetch(`${API_BASE}/v1/classes/${classId}/members`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ student_email: studentEmail }),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the them thanh vien");
  }
  return (await res.json()) as UserSummary[];
}

export async function removeClassMember(
  token: string,
  classId: string,
  studentEmail: string,
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/v1/classes/${classId}/members/${encodeURIComponent(studentEmail)}`,
    { method: "DELETE", headers: authHeaders(token) },
  );
  if (!res.ok) {
    throw await parseError(res, "Khong the xoa thanh vien");
  }
}

export async function createClassAssignment(
  token: string,
  classId: string,
  input: AssignmentCreateInput,
): Promise<Assignment> {
  const res = await fetch(`${API_BASE}/v1/classes/${classId}/assignments`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the giao bai");
  }
  return (await res.json()) as Assignment;
}

export async function deleteClassAssignment(
  token: string,
  classId: string,
  assignmentId: string,
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/v1/classes/${classId}/assignments/${assignmentId}`,
    { method: "DELETE", headers: authHeaders(token) },
  );
  if (!res.ok) {
    throw await parseError(res, "Khong the xoa bai giao");
  }
}

export async function listTeacherStudents(token: string): Promise<UserSummary[]> {
  const res = await fetch(`${API_BASE}/v1/classes/teacher/students`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai danh sach hoc sinh");
  }
  return (await res.json()) as UserSummary[];
}

export async function listMyAssignments(token: string): Promise<Assignment[]> {
  const res = await fetch(`${API_BASE}/v1/assignments/me`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai bai duoc giao");
  }
  return (await res.json()) as Assignment[];
}

export async function listMyChildren(token: string): Promise<UserSummary[]> {
  const res = await fetch(`${API_BASE}/v1/parents/me/children`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai danh sach con");
  }
  return (await res.json()) as UserSummary[];
}

export async function linkParentChild(
  token: string,
  parentEmail: string,
  childEmail: string,
): Promise<UserSummary[]> {
  const res = await fetch(`${API_BASE}/v1/parents/links`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ parent_email: parentEmail, child_email: childEmail }),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the lien ket phu huynh");
  }
  return (await res.json()) as UserSummary[];
}

// --- Knowledge Base APIs ---

export async function uploadKnowledge(
  token: string,
  file: File,
  title: string,
  subject: string = "math",
  gradeLevel: string = "grade6",
): Promise<KnowledgeDocument> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);
  formData.append("subject", subject);
  formData.append("grade_level", gradeLevel);
  const res = await fetch(`${API_BASE}/v1/knowledge/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai len tai lieu");
  }
  return (await res.json()) as KnowledgeDocument;
}

export async function listKnowledge(token: string): Promise<KnowledgeDocument[]> {
  const res = await fetch(`${API_BASE}/v1/knowledge`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai danh sach tai lieu");
  }
  return (await res.json()) as KnowledgeDocument[];
}

export async function deleteKnowledge(token: string, docId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/knowledge/${docId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the xoa tai lieu");
  }
}

export async function linkKnowledgeToClass(
  token: string,
  classId: string,
  docId: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/knowledge/classes/${classId}/link`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ doc_id: docId }),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the lien ket tai lieu voi lop");
  }
}

export async function listClassKnowledge(
  token: string,
  classId: string,
): Promise<KnowledgeDocument[]> {
  const res = await fetch(`${API_BASE}/v1/knowledge/classes/${classId}/docs`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    return [];
  }
  return (await res.json()) as KnowledgeDocument[];
}

// --- Student Memory APIs ---

export async function getStudentProfile(
  token: string,
  studentEmail: string,
): Promise<StudentProfile> {
  const res = await fetch(`${API_BASE}/v1/memory/profile/${encodeURIComponent(studentEmail)}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai ho so hoc sinh");
  }
  return (await res.json()) as StudentProfile;
}

export async function updateStudentProfile(
  token: string,
  studentEmail: string,
  input: Partial<StudentProfile>,
): Promise<StudentProfile> {
  const res = await fetch(`${API_BASE}/v1/memory/profile/${encodeURIComponent(studentEmail)}`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the cap nhat ho so hoc sinh");
  }
  return (await res.json()) as StudentProfile;
}

export async function listLearningMemories(
  token: string,
  studentEmail: string,
): Promise<LearningMemory[]> {
  const res = await fetch(`${API_BASE}/v1/memory/memories/${encodeURIComponent(studentEmail)}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    return [];
  }
  return (await res.json()) as LearningMemory[];
}

export async function listSkillAssessments(
  token: string,
  studentEmail: string,
): Promise<SkillAssessment[]> {
  const res = await fetch(`${API_BASE}/v1/memory/skills/${encodeURIComponent(studentEmail)}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    return [];
  }
  return (await res.json()) as SkillAssessment[];
}

// --- Voice Profile APIs ---

export async function createVoiceProfile(
  token: string,
  voiceName: string,
  provider: string = "gtts",
): Promise<VoiceProfile> {
  const res = await fetch(`${API_BASE}/v1/voice/profiles`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ voice_name: voiceName, provider }),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tao voice profile");
  }
  return (await res.json()) as VoiceProfile;
}

export async function listVoiceProfiles(token: string): Promise<VoiceProfile[]> {
  const res = await fetch(`${API_BASE}/v1/voice/profiles`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai danh sach voice");
  }
  return (await res.json()) as VoiceProfile[];
}

export async function uploadVoiceSample(
  token: string,
  profileId: string,
  file: File,
): Promise<{ status: string; sample_count: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/v1/voice/profiles/${profileId}/upload-sample`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the tai len mau giong noi");
  }
  return (await res.json()) as { status: string; sample_count: string };
}

export async function trainVoiceProfile(
  token: string,
  profileId: string,
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/v1/voice/profiles/${profileId}/train`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the training voice");
  }
  return (await res.json()) as { status: string };
}

export async function deleteVoiceProfile(
  token: string,
  profileId: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/voice/profiles/${profileId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the xoa voice profile");
  }
}

export async function assignVoiceToClass(
  token: string,
  classId: string,
  voiceProfileId: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/voice/classes/${classId}/voice`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ voice_profile_id: voiceProfileId }),
  });
  if (!res.ok) {
    throw await parseError(res, "Khong the gan voice cho lop");
  }
}

export { ApiError };
