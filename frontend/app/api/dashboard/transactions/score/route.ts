import { NextRequest, NextResponse } from "next/server";

import { DashboardConfigError, fraudLensRequest, requestId } from "@/lib/server-api";

export async function POST(request: NextRequest) {
  try {
    const response = await fraudLensRequest("/v1/transactions/score", { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": request.headers.get("idempotency-key") ?? `dashboard_${crypto.randomUUID()}`, "X-Correlation-ID": requestId(request) }, body: await request.text() });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: { code: error instanceof DashboardConfigError ? "DASHBOARD_NOT_CONFIGURED" : "API_UNREACHABLE", message: error instanceof Error ? error.message : "The FraudLens API could not be reached." } }, { status: 503 });
  }
}
