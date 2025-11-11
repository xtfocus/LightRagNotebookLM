import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
  ExperimentalEmptyAdapter,
  copilotKitEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";
import { NextRequest } from "next/server";

const serviceAdapter = new ExperimentalEmptyAdapter();

export const POST = async (req: NextRequest) => {
  if (!process.env.AGENT_URL) {
    throw new Error("AGENT_URL environment variable is not set");
  }

  const runtime = new CopilotRuntime({
    remoteEndpoints: [
      copilotKitEndpoint({
        url: `${process.env.AGENT_URL}/copilotkit`,
      }),
    ],
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
}; 