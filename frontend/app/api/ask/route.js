import { NextResponse } from "next/server";

import { proxyPythonJson } from "@/lib/python-api";

export const dynamic = "force-dynamic";

export async function POST(request) {
  try {
    const body = await request.json();
    const payload = await proxyPythonJson("/api/ask", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
