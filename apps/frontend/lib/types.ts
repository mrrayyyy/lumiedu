export type Role = "admin" | "teacher" | "student" | "parent";

export type Session = {
  session_id: string;
  learner_id: string;
  lesson_topic: string;
  created_at: string;
  status: string;
};

export type SessionListResponse = {
  sessions: Session[];
  total: number;
};

export type Turn = {
  transcript: string;
  assistant_response: string;
  audio_url: string;
  response_ms: number;
};

export type TurnHistoryItem = {
  transcript: string;
  assistant_response: string;
  created_at: string;
};

export type ProgressData = {
  learner_id: string;
  total_sessions: number;
  total_turns: number;
  avg_latency_ms: number;
  topics_studied: string[];
  recent_sessions: Session[];
};

export type Metrics = {
  turn_total: number;
  turn_error_total: number;
  e2e_latency_ms_last: number;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  email: string;
  role: Role;
  full_name: string;
};

export type UserSummary = {
  email: string;
  role: Role;
  full_name: string;
  grade_level?: string | null;
  is_active: boolean;
};

export type UserListResponse = {
  users: UserSummary[];
  total: number;
};

export type UserCreateInput = {
  email: string;
  password: string;
  role: Role;
  full_name: string;
  grade_level?: string | null;
};

export type UserUpdateInput = {
  role?: Role;
  full_name?: string;
  grade_level?: string | null;
  is_active?: boolean;
  password?: string;
};

export type ClassSummary = {
  class_id: string;
  name: string;
  description: string;
  teacher_email: string;
  teacher_name: string;
  member_count: number;
  created_at: string;
};

export type Assignment = {
  assignment_id: string;
  class_id: string;
  class_name: string;
  lesson_topic: string;
  description: string;
  due_at: string | null;
  created_at: string;
};

export type ClassDetail = ClassSummary & {
  members: UserSummary[];
  assignments: Assignment[];
};

export type ClassCreateInput = {
  name: string;
  description: string;
  teacher_email?: string;
};

export type AssignmentCreateInput = {
  lesson_topic: string;
  description: string;
  due_at?: string | null;
};
