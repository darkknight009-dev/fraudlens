import { NextRequest, NextResponse } from "next/server";

import { DashboardConfigError, fraudLensRequest, requestId } from "@/lib/server-api";

function failure(error: unknown) {
  return NextResponse.json({ error: { code: error instanceof DashboardConfigError ? "DASHBOARD_NOT_CONFIGURED" : "API_UNREACHABLE", message: error instanceof Error ? error.message : "The FraudLens API could not be reached." } }, { status: 503 });
}

export async function GET(request: NextRequest) {
  try {
    const response = await fraudLensRequest("/v1/config/rules", { headers: { "X-Correlation-ID": requestId(request) } });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) { return failure(error); }
}

export async function PUT(request: NextRequest) {
  try {
    const response = await fraudLensRequest("/v1/config/rules", { method: "PUT", headers: { "Content-Type": "application/json", "X-Correlation-ID": requestId(request) }, body: await request.text() });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) { return failure(error); }
}
