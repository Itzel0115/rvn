import { NextResponse } from "next/server";

import { proxyPythonJson } from "@/lib/python-api";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const payload = await proxyPythonJson("/api/chart-catalog");
    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
