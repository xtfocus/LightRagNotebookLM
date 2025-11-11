import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

export const POST = async (req: NextRequest) => {
  if (!process.env.AGENT_AGUI_URL) {
    throw new Error("AGENT_AGUI_URL environment variable is not set");
  }
  
  // Register the notebook chat agent
  // Extract the base URL without the chat-agui path
  const baseUrl = process.env.AGENT_AGUI_URL.replace(/\/chat-agui\/?$/, ''); // Remove chat-agui path
  const notebookChatAgent = new HttpAgent({
    url: `${baseUrl}/notebook-chat`,
  });
  
  const runtime = new CopilotRuntime({
    agents: {
      "notebook": notebookChatAgent,
    },
  });
  
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/notebook-chat",
  });
  
  return handleRequest(req);
}; 