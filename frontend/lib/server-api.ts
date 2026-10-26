import type { NextRequest } from "next/server";

const apiUrl = process.env.FRAUDLENS_API_URL ?? "http://localhost:8000";
const apiKey = process.env.FRAUDLENS_DASHBOARD_API_KEY;

export class DashboardConfigError extends Error {
  constructor() {
    super("Dashboard API credentials are not configured on the server.");
    this.name = "DashboardConfigError";
  }
}

export function dashboardApiConfigured(): boolean {
  return Boolean(apiKey);
}

export async function fraudLensRequest(path: string, init: RequestInit = {}): Promise<Response> {
  if (!apiKey) throw new DashboardConfigError();

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${apiKey}`);
  headers.set("Accept", "application/json");

  return fetch(`${apiUrl.replace(/\/$/, "")}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export function requestId(request: NextRequest): string {
  return request.headers.get("x-correlation-id") ?? `dashboard_${crypto.randomUUID()}`;
}
