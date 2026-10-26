import { NextResponse } from "next/server";

import { dashboardApiConfigured, fraudLensRequest } from "@/lib/server-api";

export async function GET() {
  if (!dashboardApiConfigured()) {
    return NextResponse.json({ api: "not_ready", configured: false }, { status: 503 });
  }

  try {
    const response = await fetch(
      `${(process.env.FRAUDLENS_API_URL ?? "http://localhost:8000").replace(/\/$/, "")}/health/ready`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return NextResponse.json({ api: "not_ready", configured: true, detail: "The FraudLens API is not ready." }, { status: 503 });
    }
    const authProbe = await fraudLensRequest("/v1/alerts?limit=1");
    if (authProbe.status === 401) {
      return NextResponse.json({ api: "not_ready", configured: true, auth: "invalid", detail: "The dashboard key is invalid, expired, or revoked." }, { status: 503 });
    }
    if (authProbe.status === 403) {
      return NextResponse.json({ api: "not_ready", configured: true, auth: "forbidden", detail: "The dashboard key lacks the cases:read scope." }, { status: 503 });
    }
    return NextResponse.json({ api: "ready", configured: true, auth: "ok" });
  } catch {
    return NextResponse.json({ api: "unreachable", configured: true, detail: "The FraudLens API could not be reached." }, { status: 503 });
  }
}
