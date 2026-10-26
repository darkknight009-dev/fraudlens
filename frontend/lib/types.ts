export type AlertStatus = "open" | "in_review" | "resolved" | "false_positive" | "escalated";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type RiskSignal = {
  reason_code: string;
  message: string;
  source: "rule" | "model" | "feature";
  severity: RiskLevel;
  evidence: Record<string, unknown>;
  contribution: number;
};

export type Alert = {
  id: string;
  tenant_id: string;
  assessment_id: string;
  transaction_id: string;
  status: AlertStatus;
  priority: number;
  assigned_to: string | null;
  disposition: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  assessment: {
    risk_score: number;
    risk_level: RiskLevel;
  } | null;
  notes: CaseNote[];
};

export type CaseNote = {
  id: string;
  author_id: string | null;
  body: string;
  created_at: string;
};

export type PaginatedAlerts = {
  items: Alert[];
  limit: number;
  offset: number;
  total: number;
};

export type ApiError = {
  error?: {
    code?: string;
    message?: string;
    request_id?: string;
  };
  message?: string;
};

export type DashboardStatus = {
  api: "ready" | "not_ready" | "unreachable";
  configured: boolean;
  auth?: "ok" | "invalid" | "forbidden";
  detail?: string;
};

export type Assessment = {
  assessment_id: string;
  transaction_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  mode: string;
  assessment_status: string;
  signals: RiskSignal[];
  detector_status: Record<string, string>;
  rule_set_version: string;
  model_version: string | null;
  request_id: string;
};

export type AuditEvent = {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  request_id: string | null;
  details_redacted: Record<string, unknown>;
  created_at: string;
};

export type RuleConfiguration = {
  version: string;
  amount: { threshold_minor: number; contribution: number };
  velocity: { window_minutes: number; threshold: number; contribution: number };
  provider_status: { statuses: string[]; contribution: number };
  levels: { medium: number; high: number; critical: number };
};

export type WebhookEndpoint = {
  id: string;
  url: string;
  subscriptions: string[];
  is_active: boolean;
  created_at: string;
  secret?: string | null;
};

export type WebhookDelivery = {
  id: string;
  endpoint_id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempt_count: number;
  last_status_code: number | null;
  next_attempt_at: string | null;
  delivered_at: string | null;
};
