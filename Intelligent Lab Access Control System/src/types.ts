// ================================================================
//  types.ts — shared TypeScript interfaces
// ================================================================

export interface UserEntry {
  id: number;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  embedding_count: number;
  total_attempts: number;
  last_seen: string | null;
  created_at: string;
}

export interface LogEntry {
  id: number;
  user_id: number | null;
  user_name: string | null;
  lab_id: number;
  outcome: "ALLOW" | "DENY";
  similarity_score: number | null;
  latency_ms: number | null;
  created_at: string;
}

export interface LogStats {
  total_attempts: number;
  total_allow: number;
  total_deny: number;
  allow_rate: number;
  avg_score_allow: number | null;
  avg_score_deny: number | null;
  avg_latency_ms: number | null;
  min_latency_ms: number | null;
  max_latency_ms: number | null;
}

export interface LiveEvent {
  id: number | null;
  outcome: "ALLOW" | "DENY";
  similarity_score: number | null;
  latency_ms: number | null;
  user_id: number | null;
  lab_id: number;
  created_at: string;
}

export interface ScoreBin {
  range: string;
  count: number;
}
