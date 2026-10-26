import { NextRequest, NextResponse } from "next/server";

import { DashboardConfigError, fraudLensRequest, requestId } from "@/lib/server-api";
import type { ApiError } from "@/lib/types";

export async function GET(request: NextRequest) {
  const search = request.nextUrl.searchParams;
  const query = new URLSearchParams({
    limit: search.get("limit") ?? "100",
    offset: search.get("offset") ?? "0",
  });
  const status = search.get("status");
  if (status) query.set("status", status);

  try {
    const response = await fraudLensRequest(`/v1/alerts?${query.toString()}`, {
      headers: { "X-Correlation-ID": requestId(request) },
    });
    const body = await response.json() as unknown;
    return NextResponse.json(body, { status: response.status });
  } catch (error) {
    const body: ApiError = {
      error: {
        code: error instanceof DashboardConfigError ? "DASHBOARD_NOT_CONFIGURED" : "API_UNREACHABLE",
        message: error instanceof Error ? error.message : "The FraudLens API could not be reached.",
      },
    };
    return NextResponse.json(body, { status: 503 });
  }
}
