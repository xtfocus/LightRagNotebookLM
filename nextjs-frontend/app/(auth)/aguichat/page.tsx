"use client";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit, useCoAgentStateRender } from "@copilotkit/react-core";
import dynamic from "next/dynamic";
import { AGUI_AGENT_NAME } from "../../agentConfig";
const CopilotSidebar = dynamic(
  () => import("@copilotkit/react-ui").then((mod) => mod.CopilotSidebar),
  { ssr: false }
);
import React from "react";
import { Progress } from "../../../components/ui/progress";

export default function AguichatPage() {
  // Render agent progress logs if present
  const maybeProgress = useCoAgentStateRender<any>({
    name: AGUI_AGENT_NAME,
    render: ({ state }) => {
      if (state?.logs?.length > 0) {
        return <Progress logs={state.logs} />;
      }
      return null;
    },
  });

  return (
    <div className="flex flex-col items-center justify-center h-full w-full max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">AG-UI Chat</h1>
      {maybeProgress ?? null}
      <CopilotSidebar
        labels={{
          title: "AG-UI Chat Assistant",
          initial: "Hi! How can I assist you today?",
        }}
        defaultOpen={true}
      />
    </div>
  );
}