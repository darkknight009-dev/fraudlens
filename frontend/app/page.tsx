"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  Alert,
  AlertStatus,
  ApiError,
  DashboardStatus,
  RiskLevel,
} from "@/lib/types";
import { AuditView, CheckoutView, OverviewView, RulesView, TransactionsView, WebhooksView } from "@/app/components/OperationsViews";

type Filter = AlertStatus | "all";
type View = "overview" | "checkout" | "alerts" | "transactions" | "rules" | "audit" | "webhooks";

const statusLabels: Record<AlertStatus, string> = {
  open: "Open",
  in_review: "In review",
  resolved: "Resolved",
  false_positive: "False positive",
  escalated: "Escalated",
};

const riskLabels: Record<RiskLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

const navItems = [
  { label: "Overview", icon: "grid", view: "overview" },
  { label: "Checkout", icon: "cart", view: "checkout" },
  { label: "Alert queue", icon: "radar", view: "alerts" },
  { label: "Transactions", icon: "pulse", view: "transactions" },
  { label: "Rules", icon: "sliders", view: "rules" },
  { label: "Audit trail", icon: "list", view: "audit" },
  { label: "Webhooks", icon: "link", view: "webhooks" },
] as const;

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (name === "grid") return <svg {...common}><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /></svg>;
  if (name === "radar") return <svg {...common}><circle cx="12" cy="12" r="8" /><path d="M12 12 17.5 6.5M12 4v2M4 12h2M12 18v2M18 12h2" /><circle cx="12" cy="12" r="1.4" fill="currentColor" /></svg>;
  if (name === "pulse") return <svg {...common}><path d="M3 12h4l2.2-6 4.2 12 2.2-6H21" /></svg>;
  if (name === "sliders") return <svg {...common}><path d="M4 6h16M4 12h16M4 18h16" /><circle cx="8" cy="6" r="2" fill="var(--ink-2)" /><circle cx="16" cy="12" r="2" fill="var(--ink-2)" /><circle cx="10" cy="18" r="2" fill="var(--ink-2)" /></svg>;
  if (name === "list") return <svg {...common}><path d="M8 6h13M8 12h13M8 18h13" /><path d="M3 6h.01M3 12h.01M3 18h.01" /></svg>;
  if (name === "search") return <svg {...common}><circle cx="10.8" cy="10.8" r="6.5" /><path d="m16 16 5 5" /></svg>;
  if (name === "refresh") return <svg {...common}><path d="M20 11a8 8 0 0 0-14.5-4L3 10" /><path d="M3 5v5h5M4 13a8 8 0 0 0 14.5 4L21 14" /><path d="M21 19v-5h-5" /></svg>;
  if (name === "arrow") return <svg {...common}><path d="M5 12h13M13 6l6 6-6 6" /></svg>;
  if (name === "close") return <svg {...common}><path d="m6 6 12 12M18 6 6 18" /></svg>;
  if (name === "lock") return <svg {...common}><rect x="5" y="10" width="14" height="10" rx="1" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>;
  if (name === "link") return <svg {...common}><path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1" /><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.1-1.1" /></svg>;
  if (name === "cart") return <svg {...common}><path d="M4 5h2l2 11h9l3-8H7" /><circle cx="10" cy="20" r="1" fill="currentColor" /><circle cx="17" cy="20" r="1" fill="currentColor" /></svg>;
  return <svg {...common}><circle cx="12" cy="12" r="8" /></svg>;
}

function errorMessage(body: ApiError, fallback: string) {
  return body.error?.message ?? body.message ?? fallback;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function ScoreRing({ score }: { score: number }) {
  const normalized = Math.max(0, Math.min(100, score));
  const circumference = 100.53;
  return (
    <div className="score-ring" aria-label={`Risk score ${normalized} out of 100`}>
      <svg viewBox="0 0 40 40" role="img">
        <circle className="ring-track" cx="20" cy="20" r="16" />
        <circle className="ring-value" cx="20" cy="20" r="16" style={{ strokeDasharray: `${normalized * circumference / 100} ${circumference}` }} />
      </svg>
      <span><strong>{normalized}</strong><small>/100</small></span>
    </div>
  );
}

function EmptyState({ title, detail, action }: { title: string; detail: string; action?: React.ReactNode }) {
  return (
    <div className="empty-state">
      <div className="empty-mark"><span /><span /><span /></div>
      <h3>{title}</h3>
      <p>{detail}</p>
      {action}
    </div>
  );
}

export default function OperationsConsole() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeView, setActiveView] = useState<View>("alerts");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<DashboardStatus>({ api: "unreachable", configured: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [operatorOpen, setOperatorOpen] = useState(false);

  const loadStatus = useCallback(async () => {
    const response = await fetch("/api/dashboard/status", { cache: "no-store" });
    const body = await response.json() as DashboardStatus;
    setStatus(body);
  }, []);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError("");
    const query = filter === "all" ? "" : `?status=${encodeURIComponent(filter)}`;
    try {
      const response = await fetch(`/api/dashboard/alerts${query}`, { cache: "no-store" });
      const body = await response.json() as { items?: Alert[] } & ApiError;
      if (!response.ok) throw new Error(errorMessage(body, "Could not load live alerts."));
      setAlerts(body.items ?? []);
    } catch (reason) {
      setAlerts([]);
      setError(reason instanceof Error ? reason.message : "Could not load live alerts.");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  useEffect(() => {
    setSelectedId((current) => current && alerts.some((alert) => alert.id === current) ? current : alerts[0]?.id ?? null);
  }, [alerts]);

  const selected = alerts.find((alert) => alert.id === selectedId) ?? null;
  const visibleAlerts = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return alerts;
    return alerts.filter((alert) => [alert.transaction_id, alert.id, alert.status, alert.assigned_to ?? ""].some((value) => value.toLowerCase().includes(term)));
  }, [alerts, search]);
  const openCount = alerts.filter((alert) => alert.status === "open").length;
  const reviewCount = alerts.filter((alert) => alert.status === "in_review").length;
  const criticalCount = alerts.filter((alert) => (alert.assessment?.risk_score ?? alert.priority) >= 80).length;
  const activeLabel = navItems.find((item) => item.view === activeView)?.label ?? "Alert queue";

  async function updateStatus(nextStatus: AlertStatus) {
    if (!selected) return;
    setSaving(true);
    setActionError("");
    try {
      const response = await fetch(`/api/dashboard/alerts/${selected.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      const body = await response.json() as Alert & ApiError;
      if (!response.ok) throw new Error(errorMessage(body, "Status update failed."));
      setAlerts((current) => current.map((alert) => alert.id === body.id ? body : alert));
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Status update failed.");
    } finally {
      setSaving(false);
    }
  }

  async function saveNote() {
    if (!selected || !note.trim()) return;
    setSaving(true);
    setActionError("");
    try {
      const response = await fetch(`/api/dashboard/alerts/${selected.id}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: note.trim() }),
      });
      const body = await response.json() as Alert["notes"][number] & ApiError;
      if (!response.ok) throw new Error(errorMessage(body, "Note could not be saved."));
      setAlerts((current) => current.map((alert) => alert.id === selected.id ? { ...alert, notes: [...alert.notes, body] } : alert));
      setNote("");
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Note could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="console-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-symbol"><span /><span /><span /></div>
          <div><strong>FraudLens</strong><small>RISK OPERATIONS</small></div>
        </div>

        <div className="workspace-switcher">
          <span className="workspace-dot" />
          <div><small>WORKSPACE</small><strong>Operations</strong></div>
          <span className="switcher-chevron">⌄</span>
        </div>

        <nav className="nav-list" aria-label="Primary navigation">
          <span className="nav-caption">MONITOR</span>
          {navItems.map((item) => (
            <button className={`nav-item ${item.view === activeView ? "active" : ""}`} key={item.label} type="button" onClick={() => setActiveView(item.view)}>
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.label === "Alert queue" && openCount > 0 ? <em>{openCount}</em> : null}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <div className={`connection-indicator ${status.api === "ready" ? "online" : "offline"}`} />
            <div><small>API CONNECTION</small><strong>{status.api === "ready" ? "Live" : "Needs attention"}</strong></div>
            <span className="connection-pulse" />
          </div>
          <div className="operator-row"><div className="avatar">OP</div><div><strong>Operator</strong><small>Server-side access</small></div><button type="button" aria-label="Operator menu" aria-expanded={operatorOpen} onClick={() => setOperatorOpen((current) => !current)}>•••</button>{operatorOpen ? <div className="operator-menu"><strong>Console access</strong><span>API key stays server-side.</span><button type="button" onClick={() => setOperatorOpen(false)}>Close</button></div> : null}</div>
        </div>
      </aside>

      <section className="main-stage">
        <header className="topbar">
          <div className="breadcrumbs"><span>Operations</span><Icon name="arrow" size={13} /><strong>{activeLabel}</strong></div>
          <div className="topbar-actions">
            <span className="live-indicator"><i /> {status.api === "ready" ? "LIVE API" : "API OFFLINE"}</span>
            <button className="icon-button" type="button" onClick={() => { void loadStatus(); void loadAlerts(); }} aria-label="Refresh data"><Icon name="refresh" size={17} /></button>
            <div className="topbar-divider" />
            <span className="utc-label">UTC {new Date().toISOString().slice(11, 16)}</span>
          </div>
        </header>

        <div className="content-frame">
          <section className="page-intro">
            <div>
              <div className="section-kicker"><span className="kicker-line" /> RISK CONTROL ROOM</div>
              <h1>Attention, <em>ordered.</em></h1>
              <p>Prioritise the next investigation from live, explainable risk signals.</p>
            </div>
            <div className="mode-stamp"><span className="stamp-mark">S</span><div><small>DECISION MODE</small><strong>SHADOW</strong></div><span className="stamp-rule" /></div>
          </section>

          {status.api !== "ready" ? (
            <section className="setup-banner"><div className="setup-icon"><Icon name="lock" size={19} /></div><div><strong>{status.auth === "invalid" ? "Dashboard key rejected" : status.auth === "forbidden" ? "Dashboard role is missing a scope" : "Connect this console to FraudLens"}</strong><p>{status.detail ?? "Set FRAUDLENS_DASHBOARD_API_KEY in frontend/.env.local, restart Next.js, and live records will appear here."}</p></div></section>
          ) : null}

          {activeView === "alerts" || activeView === "overview" ? <section className="metrics-strip" aria-label="Live alert metrics">
            <div className="metric-cell metric-primary"><small>QUEUE TOTAL</small><strong>{loading ? "—" : alerts.length}</strong><span>Current result set</span></div>
            <div className="metric-cell"><small>OPEN</small><strong>{loading ? "—" : openCount.toString().padStart(2, "0")}</strong><span>Requires triage</span></div>
            <div className="metric-cell"><small>IN REVIEW</small><strong>{loading ? "—" : reviewCount.toString().padStart(2, "0")}</strong><span>Analyst-owned work</span></div>
            <div className="metric-cell metric-critical"><small>HIGH EXPOSURE</small><strong>{loading ? "—" : criticalCount.toString().padStart(2, "0")}</strong><span>Score 80 and above</span></div>
            <div className="metric-cell metric-note"><small>POLICY</small><strong>ADVISORY</strong><span>Merchant remains authoritative</span></div>
          </section> : null}

          {activeView === "overview" ? <OverviewView alerts={alerts} onOpenAlert={(id) => { setSelectedId(id); setActiveView("alerts"); }} onOpenQueue={() => setActiveView("alerts")} onRefresh={() => void loadAlerts()} /> : null}
          {activeView === "checkout" ? <CheckoutView /> : null}

          {activeView === "transactions" ? <TransactionsView /> : null}
          {activeView === "rules" ? <RulesView /> : null}
          {activeView === "audit" ? <AuditView /> : null}
          {activeView === "webhooks" ? <WebhooksView /> : null}

          {activeView === "alerts" ? <section className="queue-layout">
            <div className="queue-panel">
              <div className="panel-toolbar">
                <div><span className="panel-index">01</span><div><h2>Alert queue</h2><p>Live cases ranked by risk priority</p></div></div>
                <div className="toolbar-controls">
                  <label className="search-box"><Icon name="search" size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search queue" aria-label="Search alert queue" /></label>
                  <select value={filter} onChange={(event) => setFilter(event.target.value as Filter)} aria-label="Filter alert status"><option value="all">All statuses</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
                </div>
              </div>

              {error ? <div className="inline-error"><span>!</span>{error}<button type="button" onClick={() => void loadAlerts()}>Retry</button></div> : null}
              <div className="table-head"><span>RISK / TRANSACTION</span><span>STATUS</span><span>PRIORITY</span><span>CREATED</span></div>
              <div className="alert-table">
                {loading ? <div className="table-empty"><div className="loader-line" /><span>Loading live queue</span></div> : visibleAlerts.length === 0 ? <EmptyState title="No live alerts" detail={error ? "The queue could not be loaded from the API." : "When a qualifying assessment creates an alert, it will appear here."} /> : visibleAlerts.map((alert) => {
                  const score = alert.assessment?.risk_score ?? alert.priority;
                  const level = alert.assessment?.risk_level ?? (score >= 80 ? "critical" : score >= 60 ? "high" : "medium");
                  return <button type="button" className={`alert-table-row ${selectedId === alert.id ? "selected" : ""}`} key={alert.id} onClick={() => setSelectedId(alert.id)}><span className="transaction-cell"><span className={`risk-bar risk-${level}`} /><span><strong>{alert.transaction_id}</strong><small>{alert.id.slice(0, 13)}…</small></span></span><span><b className={`status-badge status-${alert.status}`}>{statusLabels[alert.status]}</b></span><span className={`priority-score priority-${level}`}>{score}</span><time>{formatDate(alert.created_at)}</time><Icon name="arrow" size={15} /></button>;
                })}
              </div>
              <div className="table-footer"><span>Showing {visibleAlerts.length} of {alerts.length} loaded alerts</span><span>Max page size 100 <i>·</i> <button type="button" onClick={() => void loadAlerts()}>Refresh queue</button></span></div>
            </div>

            <aside className="case-panel">
              {selected ? <>
                <div className="case-header"><div><span className="panel-index">02</span><span className="case-kicker">SELECTED CASE</span><h2>{selected.transaction_id}</h2></div><button type="button" className="close-case" onClick={() => setSelectedId(null)} aria-label="Close selected case"><Icon name="close" size={17} /></button></div>
                <div className="case-score"><ScoreRing score={selected.assessment?.risk_score ?? selected.priority} /><div><span className={`case-level level-${selected.assessment?.risk_level ?? "high"}`}>{riskLabels[selected.assessment?.risk_level ?? "high"]} RISK</span><h3>Assessment priority</h3><p>{selected.assessment_id.slice(0, 18)}…</p></div></div>
                <div className="case-facts"><div><small>STATUS</small><strong>{statusLabels[selected.status]}</strong></div><div><small>RULE SET</small><strong>Live version</strong></div><div><small>CREATED</small><strong>{formatDate(selected.created_at)}</strong></div><div><small>OWNER</small><strong>{selected.assigned_to ?? "Unassigned"}</strong></div></div>
                <div className="case-section"><div className="section-label"><span>RISK SIGNALS</span><b>{selected.assessment ? "TRACEABLE" : "NO ASSESSMENT"}</b></div>{selected.assessment ? <div className="signal-summary"><span className="signal-glyph">↗</span><div><strong>Assessment linked</strong><p>Open the assessment history through the API for full evidence.</p></div></div> : <p className="muted-copy">No assessment detail is attached to this alert.</p>}</div>
                <div className="case-section"><div className="section-label"><span>CASE CONTROL</span><b>WRITES AUDITED</b></div><select className="case-select" value={selected.status} disabled={saving} onChange={(event) => void updateStatus(event.target.value as AlertStatus)}>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>{actionError ? <p className="action-error">{actionError}</p> : null}</div>
                <div className="case-section notes-section"><div className="section-label"><span>ANALYST NOTES</span><b>{selected.notes.length.toString().padStart(2, "0")}</b></div>{selected.notes.length ? <div className="notes-list">{selected.notes.slice(-2).map((item) => <div className="note-item" key={item.id}><p>{item.body}</p><small>{formatDate(item.created_at)}</small></div>)}</div> : <p className="muted-copy">No notes have been recorded for this case.</p>}<div className="note-composer"><textarea value={note} onChange={(event) => setNote(event.target.value)} maxLength={4000} placeholder="Write an auditable case note…" aria-label="Write an analyst note" /><button type="button" disabled={saving || !note.trim()} onClick={() => void saveNote()}><Icon name="arrow" size={16} /> Save note</button></div></div>
              </> : <EmptyState title="Select a case" detail="Choose a live alert from the queue to inspect its operational context." />}
            </aside>
          </section> : null}
        </div>
        <footer className="console-footer"><span>FraudLens / Risk intelligence layer</span><span>Advisory only <i /> No payment decision authority</span></footer>
      </section>
    </main>
  );
}
