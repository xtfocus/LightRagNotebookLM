import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { AGUI_AGENT_NAME } from "../../agentConfig";

export const POST = async (req: NextRequest) => {
  if (!process.env.AGENT_AGUI_URL) {
    throw new Error("AGENT_AGUI_URL environment variable is not set");
  }
  // Register the AG-UI backend as an agent using object shorthand (agent name will be 'aguiAgent')
  const aguiAgent = new HttpAgent({
    url: process.env.AGENT_AGUI_URL,
  });
  const runtime = new CopilotRuntime({
    agents: {
      [AGUI_AGENT_NAME]: aguiAgent,
    },
  });
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit-agui",
  });
  return handleRequest(req);
}; 