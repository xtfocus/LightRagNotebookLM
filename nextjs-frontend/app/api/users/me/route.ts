import { NextRequest, NextResponse } from "next/server";
import { buildBackendUrl } from "@/lib/apiConfig";

export async function GET(request: NextRequest) {
  try {
    const url = new URL(buildBackendUrl("users/me"));

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        // Forward authorization header if present
        ...(request.headers.get("authorization") && {
          authorization: request.headers.get("authorization")!,
        }),
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching current user:", error);
    return NextResponse.json(
      { error: "Failed to fetch current user" },
      { status: 500 }
    );
  }
} 