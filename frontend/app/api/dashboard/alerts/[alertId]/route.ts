import { NextRequest, NextResponse } from "next/server";

import { DashboardConfigError, fraudLensRequest, requestId } from "@/lib/server-api";
import type { ApiError } from "@/lib/types";

type RouteContext = { params: Promise<{ alertId: string }> };

function failure(error: unknown) {
  const body: ApiError = {
    error: {
      code: error instanceof DashboardConfigError ? "DASHBOARD_NOT_CONFIGURED" : "API_UNREACHABLE",
      message: error instanceof Error ? error.message : "The FraudLens API could not be reached.",
    },
  };
  return NextResponse.json(body, { status: 503 });
}

export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { alertId } = await context.params;
    const response = await fraudLensRequest(`/v1/alerts/${encodeURIComponent(alertId)}`, {
      headers: { "X-Correlation-ID": requestId(request) },
    });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return failure(error);
  }
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  try {
    const { alertId } = await context.params;
    const response = await fraudLensRequest(`/v1/alerts/${encodeURIComponent(alertId)}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-Correlation-ID": requestId(request),
      },
      body: await request.text(),
    });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return failure(error);
  }
}
