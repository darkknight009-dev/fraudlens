import { NextRequest, NextResponse } from "next/server";

import { DashboardConfigError, fraudLensRequest, requestId } from "@/lib/server-api";

export async function GET(request: NextRequest) {
  try {
    const query = request.nextUrl.searchParams;
    const response = await fraudLensRequest(`/v1/audit-events?limit=${query.get("limit") ?? "100"}&offset=${query.get("offset") ?? "0"}`, { headers: { "X-Correlation-ID": requestId(request) } });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: { code: error instanceof DashboardConfigError ? "DASHBOARD_NOT_CONFIGURED" : "API_UNREACHABLE", message: error instanceof Error ? error.message : "The FraudLens API could not be reached." } }, { status: 503 });
  }
}
