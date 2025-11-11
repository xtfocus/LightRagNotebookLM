'use client';

import React from 'react';
import { Upload, ChevronUp, ArrowUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { colors, spacing, borderRadius } from '@/lib/design-system';
import { useNotebook } from '@/contexts/NotebookContext';
import dynamic from 'next/dynamic';
import { NOTEBOOK_AGENT_NAME } from '@/app/agentConfig';
import { UserMessageProps, AssistantMessageProps, InputProps, useChatContext } from '@copilotkit/react-ui';
import { Markdown } from '@copilotkit/react-ui';
import { SparklesIcon } from '@heroicons/react/24/outline';
import { useCoAgentStateRender, useCopilotReadable } from '@copilotkit/react-core';
import { Progress } from '@/components/ui/progress';

// Dynamically import CopilotChat to avoid SSR issues
const CopilotChat = dynamic(
  () => import("@copilotkit/react-ui").then((mod) => mod.CopilotChat),
  { ssr: false }
);

// Typing Indicator Component
const TypingIndicator = () => {
  return (
    <div className="flex items-center gap-1 px-4 py-3 rounded-2xl rounded-bl-md max-w-[70%]">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
      </div>
    </div>
  );
};

// Custom User Message Component
const CustomUserMessage = (props: UserMessageProps) => {
  const wrapperStyles = "flex items-end gap-2 justify-end mb-4";
  const messageStyles = "bg-blue-500 text-white py-3 px-4 rounded-2xl rounded-br-md break-words flex-shrink-0 max-w-[70%] shadow-sm";
  const avatarStyles = "bg-blue-500 shadow-sm min-h-8 min-w-8 rounded-full text-white flex items-center justify-center text-sm font-medium";

  return (
    <div className={wrapperStyles}>
      <div className={messageStyles}>{props.message}</div>
      <div className={avatarStyles}>U</div>
    </div>
  );
};

// Custom Assistant Message Component
const CustomAssistantMessage = (props: AssistantMessageProps) => {
  const { icons } = useChatContext();
  const { message, isLoading, subComponent } = props;

  const avatarStyles = "bg-gray-400 shadow-sm min-h-8 min-w-8 rounded-full text-white flex items-center justify-center";
  const messageStyles = "bg-white text-gray-900 py-3 px-4 rounded-2xl rounded-bl-md break-words flex-shrink-0 max-w-[70%] shadow-sm border border-gray-100";

  const avatar = (
    <div className={avatarStyles}>
      <SparklesIcon className="h-4 w-4" />
    </div>
  );

  // If there's a subComponent (progress), render it separately without message bubble
  if (subComponent) {
    return (
      <div className="mb-4">
        {subComponent}
      </div>
    );
  }

  return (
    <div className="flex items-end gap-2 justify-start mb-4">
      {avatar}
      <div className={messageStyles}>
        {message && <Markdown content={message || ""} />}
        {isLoading && <TypingIndicator />}
      </div>
    </div>
  );
};

// Custom Input Component
const CustomInput = ({ inProgress, onSend, isVisible }: InputProps) => {
  const handleSubmit = (value: string) => {
    if (value.trim()) onSend(value);
  };

  const wrapperStyle = "flex gap-3 p-4 border-t border-gray-200 bg-white";
  const inputStyle = "flex-1 p-3 rounded-2xl border border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 resize-none";
  const buttonStyle = "p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center";

  return (
    <div className={wrapperStyle}>
      <textarea 
        disabled={inProgress}
        placeholder="Ask me about your sources..." 
        className={inputStyle}
        rows={1}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e.currentTarget.value);
            e.currentTarget.value = '';
          }
        }}
        onInput={(e) => {
          // Auto-resize textarea
          const target = e.target as HTMLTextAreaElement;
          target.style.height = 'auto';
          target.style.height = Math.min(target.scrollHeight, 120) + 'px';
        }}
      />
      <button 
        disabled={inProgress}
        className={buttonStyle}
        onClick={(e) => {
          const input = e.currentTarget.previousElementSibling as HTMLTextAreaElement;
          handleSubmit(input.value);
          input.value = '';
          input.style.height = 'auto';
        }}
      >
        <ArrowUp className="h-4 w-4" />
      </button>
    </div>
  );
};

interface ChatAreaProps {
  notebookId?: string;
}

export function ChatArea({ notebookId }: ChatAreaProps) {
  const { sourceCount, selectedSources } = useNotebook();

  // Expose selected sources to the AI agent via CopilotKit
  useCopilotReadable({
    description: "List of currently selected source IDs for RAG retrieval",
    value: Array.from(selectedSources),
  });

  // Log selected sources for debugging
  React.useEffect(() => {
    console.log('[RAG-FRONTEND] Selected sources updated:', {
      notebookId: notebookId,
      selectedSources: Array.from(selectedSources),
      sourceCount: selectedSources.size,
      timestamp: new Date().toISOString()
    });
  }, [selectedSources, notebookId]);

  // Render agent progress logs if present (tool calling spinner)
  const maybeProgress = useCoAgentStateRender<any>({
    name: NOTEBOOK_AGENT_NAME,
    render: ({ state }) => {
      if (state?.logs?.length > 0) {
        // Blend seamlessly with chatbot background - no visible boundaries
        return (
          <div data-test-id="progress-steps">
            <div className="overflow-hidden text-sm py-2">
              {state.logs.map((log: any, index: number) => (
                <div
                  key={index}
                  data-test-id="progress-step-item"
                  className={`flex ${
                    log.done || index === state.logs.findIndex((l: any) => !l.done)
                      ? ""
                      : "opacity-50"
                  }`}
                >
                  <div className="w-8">
                    <div
                      className="w-4 h-4 bg-slate-700 flex items-center justify-center rounded-full mt-[10px] ml-[12px]"
                      data-test-id={log.done ? 'progress-step-item_done' : 'progress-step-item_loading'}
                    >
                      {log.done ? (
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-3 h-3 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                      )}
                    </div>
                    {index < state.logs.length - 1 && (
                      <div className="h-full w-[1px] bg-slate-200 ml-[20px]" />
                    )}
                  </div>
                  <div className="flex-1 flex justify-center py-2 pl-2 pr-4">
                    <div className="flex-1 flex items-center text-xs">
                      {log.message.replace(
                        /https?:\/\/[^\s]+/g,
                        (url: string) => url.length > 40 ? url.substring(0, 40 - 3) + "..." : url
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      }
      return null;
    },
  });

  return (
    <section className="chat-panel flex-1 flex flex-col bg-white rounded-lg shadow-sm overflow-hidden min-h-0" style={{ maxHeight: '100%', backgroundColor: '#ffffff' }}>
      {/* Chat Panel Header */}
      <div className="chat-panel-header flex-shrink-0 p-4 border-b border-gray-200" style={{ backgroundColor: '#ffffff' }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm font-medium text-gray-900">Chat</span>
          </div>
          <div className="text-xs text-gray-500">
            {sourceCount} source{sourceCount !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Chat Panel Content */}
      <div className="chat-panel-content flex-1 flex flex-col overflow-hidden min-h-0" style={{ backgroundColor: '#edeffa' }}>
        {sourceCount === 0 ? (
          /* No Sources State */
          <div className="chat-panel-no-sources flex-1 flex items-center justify-center overflow-y-auto min-h-0" style={{ backgroundColor: '#edeffa' }}>
            <div className="text-center">
              <button
                className="upload-icon-button w-16 h-16 rounded-full flex items-center justify-center mb-4 mx-auto hover:bg-gray-50 transition-colors"
                style={{ backgroundColor: '#e0e7ff' }}
              >
                <ChevronUp
                  className="upload-icon h-8 w-8"
                  style={{ color: colors.primary[600] }}
                />
              </button>
              <span className="add-sources-text font-medium text-gray-900 mb-4 block" style={{ fontSize: '15px' }}>
                Add a source to get started
              </span>
              <Button
                variant="outline"
                size="sm"
                className="upload-button"
                style={{
                  borderColor: '#d1d5db',
                  backgroundColor: 'white',
                  color: '#374151',
                  padding: `${spacing.sm} ${spacing.md}`,
                  borderRadius: borderRadius.md,
                }}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload a source
              </Button>
            </div>
          </div>
        ) : (
          /* Chat Interface */
          <div className="flex-1 flex flex-col min-h-0" style={{ backgroundColor: '#edeffa' }}>
            <div
              style={{
                "--copilot-kit-primary-color": "#3b82f6",
                "--copilot-kit-contrast-color": "#ffffff",
                "--copilot-kit-background-color": "#edeffa",
                "--copilot-kit-secondary-color": "#ffffff",
                "--copilot-kit-secondary-contrast-color": "#1f2937",
                "--copilot-kit-separator-color": "#e5e7eb",
                "--copilot-kit-muted-color": "#6b7280",
              } as any}
              className="h-full notebook-copilotkit-container"
            >
              <CopilotChat
                labels={{
                  title: "Notebook Assistant",
                  initial: "Hi! I can help you with your sources. What would you like to know?",
                  placeholder: "Ask me about your sources...",
                }}
                className="h-full border-none rounded-none"
                UserMessage={CustomUserMessage}
                AssistantMessage={CustomAssistantMessage}
                Input={CustomInput}
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
} 