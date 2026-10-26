"use client";

import { useEffect, useMemo, useState } from "react";

import type { Alert, Assessment, AuditEvent, ApiError, Payment, RuleConfiguration, WebhookDelivery, WebhookEndpoint } from "@/lib/types";

function message(body: ApiError, fallback: string) {
  return body.error?.message ?? body.message ?? fallback;
}

function date(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function Failure({ text, onRetry }: { text: string; onRetry?: () => void }) {
  return <div className="view-failure"><strong>REQUEST FAILED</strong><span>{text}</span>{onRetry ? <button type="button" onClick={onRetry}>Retry</button> : null}</div>;
}

export function OverviewView({ alerts, onOpenAlert, onOpenQueue, onRefresh }: { alerts: Alert[]; onOpenAlert: (id: string) => void; onOpenQueue: () => void; onRefresh: () => void }) {
  const open = alerts.filter((alert) => alert.status === "open").length;
  const review = alerts.filter((alert) => alert.status === "in_review").length;
  const resolved = alerts.filter((alert) => ["resolved", "false_positive"].includes(alert.status)).length;
  return <div className="view-stack">
    <section className="overview-grid">
      <div className="overview-hero"><span className="panel-index">00 / CONTROL ROOM</span><h2>Signal, without noise.</h2><p>This is the live operating picture for the authenticated tenant. Every number below comes from FraudLens persistence.</p><button className="dark-action" type="button" onClick={onOpenQueue}>Open live queue <span>↗</span></button></div>
      <div className="overview-stat"><small>OPEN QUEUE</small><strong>{open}</strong><span>Needs triage now</span></div>
      <div className="overview-stat"><small>IN REVIEW</small><strong>{review}</strong><span>Active analyst work</span></div>
      <div className="overview-stat"><small>CLOSED</small><strong>{resolved}</strong><span>Resolved or dismissed</span></div>
    </section>
    <section className="data-panel">
      <div className="data-panel-header"><div><span className="panel-index">01</span><h2>Latest activity</h2><p>Most recent alerts returned by the live tenant queue</p></div><button className="text-action" type="button" onClick={onOpenQueue}>Open queue ↗</button></div>
      {alerts.length === 0 ? <div className="view-empty"><h3>Nothing has entered the queue</h3><p>When the scoring service creates an alert, its first appearance will be here.</p></div> : <div className="overview-activity">{alerts.slice(0, 8).map((alert) => <button type="button" key={alert.id} onClick={() => onOpenAlert(alert.id)}><span className={`activity-mark risk-${alert.assessment?.risk_level ?? "medium"}`} /><span><strong>{alert.transaction_id}</strong><small>{alert.status.replace("_", " ")} · {date(alert.created_at)}</small></span><b>{alert.assessment?.risk_score ?? alert.priority}</b><span>↗</span></button>)}</div>}
    </section>
  </div>;
}

export function TransactionsView() {
  const [transactionId, setTransactionId] = useState("");
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [lookupError, setLookupError] = useState("");
  const [busy, setBusy] = useState(false);
  const [scoreResult, setScoreResult] = useState<Assessment | null>(null);
  const [scoreError, setScoreError] = useState("");
  const [form, setForm] = useState({ transaction_id: "", amount_minor: "", currency: "", occurred_at: "", account_ref: "", device_ref: "", merchant_ref: "", channel: "", provider_status: "" });

  async function lookup() {
    if (!transactionId.trim()) return;
    setBusy(true); setLookupError("");
    try {
      const response = await fetch(`/api/dashboard/transactions/${encodeURIComponent(transactionId.trim())}/assessments`, { cache: "no-store" });
      const body = await response.json() as { items?: Assessment[] } & ApiError;
      if (!response.ok) throw new Error(message(body, "Transaction lookup failed."));
      setAssessments(body.items ?? []);
    } catch (error) { setAssessments([]); setLookupError(error instanceof Error ? error.message : "Transaction lookup failed."); } finally { setBusy(false); }
  }

  async function score(event: React.FormEvent) {
    event.preventDefault(); setScoreError(""); setScoreResult(null);
    try {
      const response = await fetch("/api/dashboard/transactions/score", { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": `console_${crypto.randomUUID()}` }, body: JSON.stringify({ ...form, amount_minor: Number(form.amount_minor), occurred_at: new Date(form.occurred_at).toISOString(), device_ref: form.device_ref || null, merchant_ref: form.merchant_ref || null, provider_status: form.provider_status || null, metadata: { source: "dashboard" } }) });
      const body = await response.json() as Assessment & ApiError;
      if (!response.ok) throw new Error(message(body, "Transaction could not be scored."));
      setScoreResult(body);
    } catch (error) { setScoreError(error instanceof Error ? error.message : "Transaction could not be scored."); }
  }

  const setField = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm((current) => ({ ...current, [key]: event.target.value }));
  return <div className="view-stack">
    <section className="view-heading"><div><span className="panel-index">03 / TRANSACTION INTELLIGENCE</span><h2>Trace a transaction.</h2><p>Look up persisted assessments or run a live advisory assessment through the authenticated tenant.</p></div></section>
    <section className="transaction-workspace">
      <div className="data-panel lookup-panel"><div className="data-panel-header"><div><span className="panel-index">01</span><h2>Assessment history</h2><p>Tenant-scoped and paginated by the API</p></div></div><div className="lookup-form"><input value={transactionId} onChange={(event) => setTransactionId(event.target.value)} placeholder="Transaction ID" aria-label="Transaction ID" /><button type="button" className="dark-action" onClick={() => void lookup()} disabled={busy}>{busy ? "Looking up…" : "Look up"}<span>↗</span></button></div>{lookupError ? <Failure text={lookupError} /> : null}{assessments.length === 0 && !lookupError ? <div className="view-empty compact"><h3>No transaction loaded</h3><p>Enter an existing transaction ID to inspect its assessment history.</p></div> : <div className="assessment-list">{assessments.map((assessment) => <div className="assessment-row" key={assessment.assessment_id}><div><strong>{assessment.assessment_id}</strong><small>{assessment.request_id} · {assessment.rule_set_version}</small></div><b className={`priority-score priority-${assessment.risk_level}`}>{assessment.risk_score}</b><span>{assessment.risk_level}</span></div>)}</div>}</div>
      <form className="data-panel score-form" onSubmit={score}><div className="data-panel-header"><div><span className="panel-index">02</span><h2>Run assessment</h2><p>Advisory only. No payment outcome is changed.</p></div><span className="form-mode">SHADOW</span></div><div className="form-grid">{([ ["transaction_id", "Transaction ID", "text"], ["amount_minor", "Amount minor", "number"], ["currency", "Currency", "text"], ["occurred_at", "Occurred at", "datetime-local"], ["account_ref", "Account reference", "text"], ["device_ref", "Device reference", "text"], ["merchant_ref", "Merchant reference", "text"] ] as const).map(([key, label, type]) => <label key={key}>{label}<input required={!["device_ref", "merchant_ref"].includes(key)} type={type} value={form[key]} onChange={setField(key)} /></label>)}<label>Channel<select required value={form.channel} onChange={setField("channel")}><option value="">Select channel</option><option value="card">Card</option><option value="bank_transfer">Bank transfer</option><option value="wallet">Wallet</option><option value="upi">UPI</option><option value="other">Other</option></select></label><label>Provider status<input value={form.provider_status} onChange={setField("provider_status")} /></label></div>{scoreError ? <Failure text={scoreError} /> : null}<button className="dark-action full-action" type="submit">Score transaction <span>↗</span></button>{scoreResult ? <div className="score-result"><strong>{scoreResult.risk_score}/100</strong><span>{scoreResult.risk_level} · {scoreResult.assessment_status} · {scoreResult.mode}</span></div> : null}</form>
    </section>
  </div>;
}

export function CheckoutView() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [selected, setSelected] = useState<Payment | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ merchant_order_id: "", amount_minor: "", currency: "INR", account_ref: "", device_ref: "", channel: "upi", payment_method: "test_approved" });

  async function load() {
    setError("");
    const response = await fetch("/api/dashboard/payments?limit=50", { cache: "no-store" });
    const body = await response.json() as { items?: Payment[] } & ApiError;
    if (!response.ok) throw new Error(message(body, "Payment history could not be loaded."));
    setPayments(body.items ?? []);
  }

  useEffect(() => { void load().catch((reason) => setError(reason instanceof Error ? reason.message : "Payment history could not be loaded.")); }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setSelected(null);
    try {
      const response = await fetch("/api/dashboard/payments", { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": `checkout_${crypto.randomUUID()}` }, body: JSON.stringify({ ...form, amount_minor: Number(form.amount_minor), device_ref: form.device_ref || null, metadata: { source: "sandbox_checkout" } }) });
      const body = await response.json() as Payment & ApiError;
      if (!response.ok) throw new Error(message(body, "Payment could not be processed."));
      setSelected(body); setPayments((current) => [body, ...current]);
      setForm((current) => ({ ...current, merchant_order_id: "", amount_minor: "", account_ref: "", device_ref: "" }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Payment could not be processed."); } finally { setBusy(false); }
  }

  const setField = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm((current) => ({ ...current, [key]: event.target.value }));
  const money = (payment: Payment) => `${payment.currency} ${(payment.amount_minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  return <div className="view-stack">
    <section className="view-heading"><div><span className="panel-index">07 / SANDBOX CHECKOUT</span><h2>Watch the payment happen.</h2><p>A complete local payment journey: checkout, mock gateway, FraudLens assessment, merchant policy, and final outcome.</p></div><span className="form-mode">NO REAL MONEY</span></section>
    <section className="checkout-layout">
      <form className="data-panel checkout-form" onSubmit={submit}><div className="data-panel-header"><div><span className="panel-index">01</span><h2>Customer checkout</h2><p>Uses safe synthetic payment methods only.</p></div><span className="form-mode">TEST RAIL</span></div><div className="checkout-amount"><small>PAYMENT AMOUNT</small><div><span>₹</span><input required type="number" min="1" value={form.amount_minor} onChange={setField("amount_minor")} placeholder="250000" /><em>minor units</em></div></div><div className="form-grid checkout-grid"><label>Merchant order<input required value={form.merchant_order_id} onChange={setField("merchant_order_id")} placeholder="order_10001" /></label><label>Currency<select value={form.currency} onChange={setField("currency")}><option>INR</option><option>USD</option><option>EUR</option></select></label><label>Account reference<input required value={form.account_ref} onChange={setField("account_ref")} placeholder="acct_customer_001" /></label><label>Device reference<input value={form.device_ref} onChange={setField("device_ref")} placeholder="device_browser_001" /></label><label>Channel<select value={form.channel} onChange={setField("channel")}><option value="upi">UPI</option><option value="card">Card</option><option value="wallet">Wallet</option><option value="bank_transfer">Bank transfer</option></select></label><label>Test payment method<select value={form.payment_method} onChange={setField("payment_method")}><option value="test_approved">Approved test token</option><option value="test_declined">Declined test token</option><option value="test_timeout">Timeout test token</option></select></label></div>{error ? <Failure text={error} /> : null}<button className="dark-action full-action" type="submit" disabled={busy}>{busy ? "Running payment workflow…" : "Submit payment"}<span>↗</span></button><p className="checkout-footnote">This sandbox records no PAN, CVV, PIN, OTP, or bank credentials. The mock gateway outcome stays separate from the FraudLens recommendation.</p></form>
      <div className="data-panel payment-result-panel">{selected ? <><div className="data-panel-header"><div><span className="panel-index">02</span><h2>Payment lifecycle</h2><p>{selected.merchant_order_id} · {money(selected)}</p></div><span className={`payment-outcome payment-${selected.payment_status}`}>{selected.payment_status}</span></div><div className="payment-result-top"><div><small>PROVIDER OUTCOME</small><strong>{selected.provider_status}</strong><span>{selected.provider_reference}</span></div><div><small>FRAUDLENS</small><strong className={`risk-text-${selected.risk_level}`}>{selected.risk_score ?? "—"}/100</strong><span>{selected.risk_recommendation ?? "unavailable"} recommendation</span></div></div><div className="payment-timeline">{selected.timeline.map((step, index) => <div className="payment-step" key={step.name}><span className={`step-node step-${step.status}`}>{index + 1}</span><div><strong>{step.name.replaceAll("_", " ")}</strong><p>{step.detail}</p></div></div>)}</div></> : <div className="view-empty"><div className="empty-mark"><span /><span /><span /></div><h3>Your payment timeline appears here</h3><p>Submit a test payment to see the exact handoff between merchant checkout, gateway, FraudLens, and policy.</p></div>}</div>
    </section>
    <section className="data-panel"><div className="data-panel-header"><div><span className="panel-index">03</span><h2>Payment activity</h2><p>Persisted sandbox intents for this tenant</p></div><button type="button" className="text-action" onClick={() => void load()}>Refresh activity</button></div>{payments.length === 0 ? <div className="view-empty compact"><h3>No payments yet</h3><p>Payments created through this checkout will appear in this ledger.</p></div> : <div className="payment-ledger">{payments.map((payment) => <button type="button" key={payment.id} onClick={() => setSelected(payment)}><span className={`risk-bar risk-${payment.risk_level ?? "medium"}`} /><span><strong>{payment.merchant_order_id}</strong><small>{money(payment)} · {payment.provider_status} · {date(payment.created_at)}</small></span><b className={`payment-outcome payment-${payment.payment_status}`}>{payment.payment_status}</b><strong className={`priority-score priority-${payment.risk_level ?? "medium"}`}>{payment.risk_score ?? "—"}</strong></button>)}</div>}</section>
  </div>;
}

export function RulesView() {
  const [configuration, setConfiguration] = useState<RuleConfiguration | null>(null);
  const [editor, setEditor] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() { setError(""); const response = await fetch("/api/dashboard/rules", { cache: "no-store" }); const body = await response.json() as { configuration?: RuleConfiguration } & ApiError; if (!response.ok) throw new Error(message(body, "Rules could not be loaded.")); setConfiguration(body.configuration ?? null); setEditor(JSON.stringify(body.configuration ?? {}, null, 2)); }
  useEffect(() => { void load().catch((reason) => setError(reason instanceof Error ? reason.message : "Rules could not be loaded.")); }, []);
  async function save() { setBusy(true); setSaved(""); setError(""); try { const parsed = JSON.parse(editor) as RuleConfiguration; const response = await fetch("/api/dashboard/rules", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ configuration: parsed }) }); const body = await response.json() as { configuration?: RuleConfiguration; version?: string } & ApiError; if (!response.ok) throw new Error(message(body, "Rule configuration was rejected.")); setConfiguration(body.configuration ?? null); setSaved(`Activated ${body.version ?? parsed.version}`); } catch (reason) { setError(reason instanceof Error ? reason.message : "Rule configuration was rejected."); } finally { setBusy(false); } }
  return <div className="view-stack"><section className="view-heading"><div><span className="panel-index">04 / CONTROL POLICY</span><h2>Rules with receipts.</h2><p>Every replacement is validated, versioned, and written to the tenant audit trail.</p></div></section><section className="rules-workspace"><div className="data-panel rule-reference"><div className="data-panel-header"><div><span className="panel-index">01</span><h2>Active configuration</h2><p>{configuration?.version ?? "Loading active version…"}</p></div></div>{configuration ? <div className="rule-cards"><div><small>AMOUNT THRESHOLD</small><strong>{configuration.amount.threshold_minor.toLocaleString()}</strong><span>minor units · +{configuration.amount.contribution}</span></div><div><small>VELOCITY WINDOW</small><strong>{configuration.velocity.window_minutes} min</strong><span>{configuration.velocity.threshold} events · +{configuration.velocity.contribution}</span></div><div><small>RISK LEVELS</small><strong>{configuration.levels.medium} / {configuration.levels.high} / {configuration.levels.critical}</strong><span>medium · high · critical</span></div><div><small>PROVIDER STATES</small><strong>{configuration.provider_status.statuses.join(", ")}</strong><span>+{configuration.provider_status.contribution} contribution</span></div></div> : <div className="view-empty compact"><h3>No configuration loaded</h3></div>}</div><div className="data-panel rule-editor"><div className="data-panel-header"><div><span className="panel-index">02</span><h2>Publish a version</h2><p>Use the strict RuleConfiguration schema.</p></div><span className="form-mode">AUDITED WRITE</span></div><textarea className="json-editor" value={editor} onChange={(event) => setEditor(event.target.value)} spellCheck={false} aria-label="Rule configuration JSON" />{error ? <Failure text={error} /> : null}{saved ? <div className="success-line">{saved}</div> : null}<div className="editor-actions"><button type="button" className="text-action" onClick={() => void load()}>Discard changes</button><button type="button" className="dark-action" disabled={busy || !editor} onClick={() => void save()}>{busy ? "Publishing…" : "Publish version"}<span>↗</span></button></div></div></section></div>;
}

export function AuditView() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  async function load() { setError(""); const response = await fetch("/api/dashboard/audit?limit=100", { cache: "no-store" }); const body = await response.json() as { items?: AuditEvent[] } & ApiError; if (!response.ok) throw new Error(message(body, "Audit events could not be loaded.")); setEvents(body.items ?? []); }
  useEffect(() => { void load().catch((reason) => setError(reason instanceof Error ? reason.message : "Audit events could not be loaded.")); }, []);
  const filtered = useMemo(() => events.filter((event) => `${event.action} ${event.target_type} ${event.target_id ?? ""}`.toLowerCase().includes(search.toLowerCase())), [events, search]);
  return <div className="view-stack"><section className="view-heading"><div><span className="panel-index">05 / FORENSICS</span><h2>Audit, not assumptions.</h2><p>An append-oriented view of security-sensitive actions in this tenant.</p></div><button type="button" className="dark-action" onClick={() => void load()}>Refresh trail <span>↗</span></button></section><section className="data-panel"><div className="data-panel-header"><div><span className="panel-index">01</span><h2>Event trail</h2><p>{events.length} events loaded</p></div><label className="search-box audit-search"><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter actions" aria-label="Filter audit actions" /></label></div>{error ? <Failure text={error} onRetry={() => void load()} /> : filtered.length === 0 ? <div className="view-empty"><h3>No matching audit events</h3><p>Events will appear after authenticated writes and case actions occur.</p></div> : <div className="audit-table">{filtered.map((event) => <div className="audit-row" key={event.id}><span className="audit-time">{date(event.created_at)}</span><strong>{event.action}</strong><span>{event.target_type}</span><code>{event.target_id ?? "—"}</code><small>{event.actor_type}</small></div>)}</div>}</section></div>;
}

export function WebhooksView() {
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [form, setForm] = useState({ url: "", secret: "", subscriptions: "alert.created" });
  const [error, setError] = useState("");
  const [savedSecret, setSavedSecret] = useState("");
  async function load() { setError(""); const [endpointResponse, deliveryResponse] = await Promise.all([fetch("/api/dashboard/webhooks", { cache: "no-store" }), fetch("/api/dashboard/webhooks/deliveries", { cache: "no-store" })]); const endpointBody = await endpointResponse.json() as WebhookEndpoint[] & ApiError; const deliveryBody = await deliveryResponse.json() as WebhookDelivery[] & ApiError; if (!endpointResponse.ok) throw new Error(message(endpointBody, "Webhook endpoints could not be loaded.")); if (!deliveryResponse.ok) throw new Error(message(deliveryBody, "Webhook deliveries could not be loaded.")); setEndpoints(endpointBody); setDeliveries(deliveryBody); }
  useEffect(() => { void load().catch((reason) => setError(reason instanceof Error ? reason.message : "Webhook data could not be loaded.")); }, []);
  async function register(event: React.FormEvent) { event.preventDefault(); setError(""); setSavedSecret(""); const response = await fetch("/api/dashboard/webhooks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, subscriptions: form.subscriptions.split(",").map((item) => item.trim()).filter(Boolean) }) }); const body = await response.json() as WebhookEndpoint & ApiError; if (!response.ok) { setError(message(body, "Webhook endpoint could not be registered.")); return; } setSavedSecret(body.secret ?? ""); setForm({ url: "", secret: "", subscriptions: "alert.created" }); await load(); }
  async function replay(id: string) { const response = await fetch(`/api/dashboard/webhooks/deliveries/${id}/replay`, { method: "POST" }); const body = await response.json() as WebhookDelivery & ApiError; if (!response.ok) { setError(message(body, "Delivery could not be replayed.")); return; } setDeliveries((current) => current.map((delivery) => delivery.id === body.id ? body : delivery)); }
  return <div className="view-stack"><section className="view-heading"><div><span className="panel-index">06 / EVENT DELIVERY</span><h2>Outbound, controlled.</h2><p>Signed delivery endpoints, attempts, and dead-letter replay for this tenant.</p></div></section><section className="webhook-grid"><form className="data-panel webhook-form" onSubmit={register}><div className="data-panel-header"><div><span className="panel-index">01</span><h2>Register endpoint</h2><p>HTTPS only · secret returned once</p></div></div><label>HTTPS endpoint<input type="url" required value={form.url} onChange={(event) => setForm({ ...form, url: event.target.value })} placeholder="https://your-system.example/hooks/fraud" /></label><label>Signing secret<input type="password" required minLength={32} value={form.secret} onChange={(event) => setForm({ ...form, secret: event.target.value })} placeholder="At least 32 characters" /></label><label>Subscriptions<input required value={form.subscriptions} onChange={(event) => setForm({ ...form, subscriptions: event.target.value })} placeholder="alert.created" /></label><button className="dark-action full-action" type="submit">Register endpoint <span>↗</span></button>{savedSecret ? <div className="secret-reveal"><small>STORE THIS SECRET NOW</small><code>{savedSecret}</code></div> : null}</form><div className="data-panel delivery-panel"><div className="data-panel-header"><div><span className="panel-index">02</span><h2>Delivery ledger</h2><p>{deliveries.length} recent deliveries</p></div><button className="text-action" type="button" onClick={() => void load()}>Refresh</button></div>{error ? <Failure text={error} onRetry={() => void load()} /> : deliveries.length === 0 ? <div className="view-empty compact"><h3>No deliveries</h3><p>Queued webhook attempts will appear here.</p></div> : <div className="delivery-list">{deliveries.map((delivery) => <div className="delivery-row" key={delivery.id}><span className={`delivery-dot delivery-${delivery.status}`} /><div><strong>{delivery.event_type}</strong><small>{delivery.event_id} · {delivery.attempt_count} attempts</small></div><b>{delivery.status}</b>{["dead_letter", "failed", "retrying"].includes(delivery.status) ? <button type="button" onClick={() => void replay(delivery.id)}>Replay</button> : null}</div>)}</div>}</div></section><section className="data-panel endpoint-list"><div className="data-panel-header"><div><span className="panel-index">03</span><h2>Registered endpoints</h2><p>Secrets are never returned from list operations.</p></div></div>{endpoints.length === 0 ? <div className="view-empty compact"><h3>No endpoints registered</h3></div> : endpoints.map((endpoint) => <div className="endpoint-row" key={endpoint.id}><span className="endpoint-status" /><strong>{endpoint.url}</strong><span>{endpoint.subscriptions.join(", ")}</span><small>{date(endpoint.created_at)}</small></div>)}</section></div>;
}
