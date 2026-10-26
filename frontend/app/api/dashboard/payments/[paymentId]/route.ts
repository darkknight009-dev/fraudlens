import { NextRequest, NextResponse } from "next/server";

import { DashboardConfigError, fraudLensRequest, requestId } from "@/lib/server-api";

type RouteContext = { params: Promise<{ paymentId: string }> };

export async function GET(request: NextRequest, context: RouteContext) {
  try { const { paymentId } = await context.params; const response = await fraudLensRequest(`/v1/sandbox/payments/${encodeURIComponent(paymentId)}`, { headers: { "X-Correlation-ID": requestId(request) } }); return NextResponse.json(await response.json(), { status: response.status }); } catch (error) { return NextResponse.json({ error: { code: error instanceof DashboardConfigError ? "DASHBOARD_NOT_CONFIGURED" : "API_UNREACHABLE", message: error instanceof Error ? error.message : "The FraudLens API could not be reached." } }, { status: 503 }); }
}
