import { NextRequest, NextResponse } from "next/server";

import { DashboardConfigError, fraudLensRequest, requestId } from "@/lib/server-api";

type RouteContext = { params: Promise<{ transactionId: string }> };

export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { transactionId } = await context.params;
    const response = await fraudLensRequest(`/v1/transactions/${encodeURIComponent(transactionId)}/assessments`, { headers: { "X-Correlation-ID": requestId(request) } });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: { code: error instanceof DashboardConfigError ? "DASHBOARD_NOT_CONFIGURED" : "API_UNREACHABLE", message: error instanceof Error ? error.message : "The FraudLens API could not be reached." } }, { status: 503 });
  }
}
