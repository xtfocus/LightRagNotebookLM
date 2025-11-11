"use client";
import { CopilotKit } from "@copilotkit/react-core";
import { usePathname } from "next/navigation";
import { AGUI_AGENT_NAME, AGUI_AGENT_RUNTIME_URL, NOTEBOOK_AGENT_NAME, NOTEBOOK_AGENT_RUNTIME_URL } from "./agentConfig";

export default function ClientCopilotKitWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname.startsWith("/aguichat")) {
    return (
      <CopilotKit key={pathname} runtimeUrl={AGUI_AGENT_RUNTIME_URL} agent={AGUI_AGENT_NAME}>
        {children}
      </CopilotKit>
    );
  }
  if (pathname.startsWith("/notebooks/")) {
    return (
      <CopilotKit key={pathname} runtimeUrl={NOTEBOOK_AGENT_RUNTIME_URL} agent={NOTEBOOK_AGENT_NAME}>
        {children}
      </CopilotKit>
    );
  }
  // For all other routes, just render children without CopilotKit context
  return <>{children}</>;
} 