import { NextRequest, NextResponse } from "next/server";
import { buildBackendUrl } from "@/lib/apiConfig";

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const dryRun = searchParams.get("dry_run") === "true";
    
    const url = new URL(buildBackendUrl(`uploads/cleanup/orphaned-files`));
    url.searchParams.set("dry_run", dryRun.toString());

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Forward authorization header if present
        ...(request.headers.get("authorization") && {
          authorization: request.headers.get("authorization")!,
        }),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || "Failed to cleanup orphaned files" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error cleaning up orphaned files:", error);
    return NextResponse.json(
      { error: "Failed to cleanup orphaned files" },
      { status: 500 }
    );
  }
}
