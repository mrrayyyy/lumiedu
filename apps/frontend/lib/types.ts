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
};
