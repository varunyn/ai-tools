"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import type { ToolUIPart } from "ai";
import dynamic from "next/dynamic";
import { use, useState, useMemo, useEffect } from "react";
import useSWR from "swr";
import {
  ModelSelector,
  ModelSelectorContent,
  ModelSelectorEmpty,
  ModelSelectorGroup,
  ModelSelectorInput,
  ModelSelectorItem,
  ModelSelectorList,
  ModelSelectorLogo,
  ModelSelectorLogoGroup,
  ModelSelectorName,
  ModelSelectorTrigger,
} from "@/components/ai-elements/model-selector";
import { Suggestion, Suggestions } from "@/components/ai-elements/suggestion";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageActions,
  MessageAction,
} from "@/components/ai-elements/message";
import {
  Tool,
  ToolContent,
  ToolHeader,
  ToolInput,
  ToolOutput,
} from "@/components/ai-elements/tool";
import { CheckIcon, CopyIcon } from "lucide-react";
import type { BundledLanguage } from "shiki";

const CodeBlock = dynamic(
  () =>
    import("@/components/ai-elements/code-block").then((m) => ({
      default: m.CodeBlock,
    })),
  { ssr: false },
);
const CodeBlockCopyButton = dynamic(
  () =>
    import("@/components/ai-elements/code-block").then((m) => ({
      default: m.CodeBlockCopyButton,
    })),
  { ssr: false },
);

type ChatMessage = {
  id?: string;
  role: "system" | "user" | "assistant";
  parts?: unknown;
};

function isTextPart(part: unknown): part is { type: "text"; text: string } {
  if (typeof part !== "object" || part === null) return false;
  const o = part as Record<string, unknown>;
  return o.type === "text" && typeof o.text === "string";
}

function isToolPart(part: unknown): part is ToolUIPart {
  if (typeof part !== "object" || part === null) return false;
  const o = part as Record<string, unknown>;
  return (
    typeof o.type === "string" &&
    o.type.startsWith("tool-") &&
    typeof o.state === "string"
  );
}

type MarkdownPart =
  | string
  | {
      type: "code";
      language: BundledLanguage;
      code: string;
    };

function normalizeMessageParts(
  rawParts: unknown,
):
  | Array<{ kind: "text"; text: string } | { kind: "tool"; tool: ToolUIPart }>
  | [] {
  if (!Array.isArray(rawParts)) return [];

  const normalized: Array<
    { kind: "text"; text: string } | { kind: "tool"; tool: ToolUIPart }
  > = [];

  for (const part of rawParts) {
    if (isTextPart(part)) {
      const last = normalized.at(-1);
      if (last?.kind === "text") {
        last.text += part.text;
      } else {
        normalized.push({ kind: "text", text: part.text });
      }
      continue;
    }

    if (isToolPart(part)) {
      normalized.push({ kind: "tool", tool: part });
    }
  }

  return normalized;
}

function getConcatenatedTextFromNormalizedParts(
  parts: Array<
    { kind: "text"; text: string } | { kind: "tool"; tool: ToolUIPart }
  >,
): string {
  return parts.map((p) => (p.kind === "text" ? p.text : "")).join("");
}

const CODE_BLOCK_REGEX = /```(\w+)?\n([\s\S]*?)```/g;

function renderMarkdownWithCodeBlocks(content: string) {
  const parts: MarkdownPart[] = [];
  let lastIndex = 0;
  let match;
  let hasCodeBlocks = false;

  CODE_BLOCK_REGEX.lastIndex = 0;

  while ((match = CODE_BLOCK_REGEX.exec(content)) !== null) {
    hasCodeBlocks = true;

    if (match.index > lastIndex) {
      const textBefore = content.substring(lastIndex, match.index).trim();
      if (textBefore) {
        parts.push(textBefore);
      }
    }

    const language = (match[1] || "text").toLowerCase() as BundledLanguage;
    const code = match[2].trim();
    parts.push({ type: "code", language, code });

    lastIndex = CODE_BLOCK_REGEX.lastIndex;
  }

  if (lastIndex < content.length) {
    const textAfter = content.substring(lastIndex).trim();
    if (textAfter) {
      parts.push(textAfter);
    }
  }

  if (!hasCodeBlocks || parts.length === 0) {
    return <MessageResponse>{content}</MessageResponse>;
  }

  return (
    <>
      {parts.map((part, index) => {
        if (typeof part === "string") {
          return (
            <MessageResponse key={`text-${index}`}>{part}</MessageResponse>
          );
        } else {
          return (
            <CodeBlock
              key={`code-${index}`}
              code={part.code}
              language={part.language}
              showLineNumbers={true}
            >
              <CodeBlockCopyButton />
            </CodeBlock>
          );
        }
      })}
    </>
  );
}

const SUGGESTIONS = [
  "What are the latest trends in AI?",
  "How does machine learning work?",
  "Explain quantum computing",
  "Best practices for React development",
  "Tell me about TypeScript benefits",
  "How to optimize database queries?",
  "What is the difference between SQL and NoSQL?",
  "Explain cloud computing basics",
];

const THINKING_INDICATOR = (
  <div className="flex items-center space-x-2">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
      <div
        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
        style={{ animationDelay: "0.1s" }}
      />
      <div
        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
        style={{ animationDelay: "0.2s" }}
      />
    </div>
    <span className="text-sm text-gray-500">Thinking...</span>
  </div>
);

type BackendModel = {
  id: string;
  name: string;
  chef: string;
  chefSlug: string;
  providers: string[];
};

const modelsFetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok)
      throw new Error(
        res.status === 502 ? "Backend unreachable" : `Models ${res.status}`,
      );
    return res.json() as Promise<{ models?: BackendModel[] }>;
  });

type PageProps = {
  params?: Promise<Record<string, string | string[]>>;
  searchParams?: Promise<Record<string, string | string[]>>;
};

export default function Chat(props: PageProps) {
  use(props.params ?? Promise.resolve({}));
  use(props.searchParams ?? Promise.resolve({}));

  const [input, setInput] = useState("");
  const [userSelectedModel, setUserSelectedModel] = useState("");
  const [modelSelectorOpen, setModelSelectorOpen] = useState(false);
  const [dynamicSuggestions, setDynamicSuggestions] = useState<string[] | null>(
    null,
  );
  const [pendingSuggestion, setPendingSuggestion] = useState<string | null>(
    null,
  );
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  const {
    data: modelsData,
    error: modelsError,
    isLoading: modelsLoading,
  } = useSWR<{ models?: BackendModel[] }>("/api/models", modelsFetcher);
  const models = Array.isArray(modelsData?.models) ? modelsData.models : [];
  const modelsErrorMsg = modelsError
    ? modelsError instanceof Error
      ? modelsError.message
      : "Failed to load models"
    : null;

  const selectedModel =
    userSelectedModel && models.some((m) => m.id === userSelectedModel)
      ? userSelectedModel
      : (models[0]?.id ?? "");

  const transport = useMemo(
    () => new DefaultChatTransport({ api: "/api/chat" }),
    [],
  );
  const { messages, sendMessage, status } = useChat({
    transport,
    onFinish: (options: {
      message: { parts?: unknown };
      isAbort?: boolean;
      isError?: boolean;
    }) => {
      if (options.isAbort || options.isError) return;
      const text = getConcatenatedTextFromNormalizedParts(
        normalizeMessageParts(options.message?.parts),
      ).trim();
      if (!text || !selectedModel) return;
      setSuggestionsLoading(true);
      fetch("/api/suggestions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lastMessage: text.slice(-4000),
          model: selectedModel,
        }),
      })
        .then((r) => r.json())
        .then((data: { suggestions?: string[] }) => {
          if (Array.isArray(data.suggestions) && data.suggestions.length > 0) {
            setDynamicSuggestions(data.suggestions);
          }
          setSuggestionsLoading(false);
        })
        .catch(() => {
          setSuggestionsLoading(false);
        });
    },
    onError: (error: Error) => {
      console.error("Chat error:", error);
    },
  });

  const selectedModelData = models.find((m) => m.id === selectedModel);
  const chefGroups = [
    ...new Set(models.map((m) => m.chef).filter(Boolean)),
  ].sort();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && selectedModel) {
      sendMessage({ text: input }, { body: { model: selectedModel } });
      setInput("");
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (!selectedModel) return;
    setPendingSuggestion(suggestion);
    sendMessage({ text: suggestion }, { body: { model: selectedModel } });
  };

  useEffect(() => {
    if (!pendingSuggestion || messages.length === 0) return;
    const last = messages[messages.length - 1];
    if (last.role !== "user") return;
    const text = getConcatenatedTextFromNormalizedParts(
      normalizeMessageParts(last.parts),
    ).trim();
    if (text === pendingSuggestion.trim()) {
      queueMicrotask(() => setPendingSuggestion(null));
    }
  }, [messages, pendingSuggestion]);

  useEffect(() => {
    if (status === "error") {
      queueMicrotask(() => setPendingSuggestion(null));
    }
  }, [status]);

  const showOptimisticSuggestion =
    pendingSuggestion != null &&
    (messages.length === 0 ||
      (() => {
        const last = messages[messages.length - 1];
        if (last.role !== "user") return true;
        const lastText = getConcatenatedTextFromNormalizedParts(
          normalizeMessageParts(last.parts),
        ).trim();
        return lastText !== pendingSuggestion.trim();
      })());

  const contentWidth = "max-w-4xl xl:max-w-5xl mx-auto w-full px-4 sm:px-6";

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header - full width bar, content centered */}
      <header className="sticky top-0 z-10 shrink-0 bg-white border-b border-gray-200 shadow-sm">
        <div
          className={`${contentWidth} py-4 flex items-center justify-between`}
        >
          <div className="flex items-center gap-3">
            <img src="/oracle.svg" alt="Oracle" className="h-8 w-auto" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                OCI OpenAI Chat
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Powered by Oracle Cloud Infrastructure Generative AI
              </p>
            </div>
          </div>

          <ModelSelector
            open={modelSelectorOpen}
            onOpenChange={setModelSelectorOpen}
          >
            <ModelSelectorTrigger className="bg-white border border-gray-300 rounded-md px-3 py-1.5 text-sm font-medium flex items-center gap-2 hover:bg-gray-50 transition-colors min-w-[200px]">
              {modelsLoading ? (
                <ModelSelectorName>Loading models…</ModelSelectorName>
              ) : modelsErrorMsg ? (
                <ModelSelectorName className="text-red-600">
                  {modelsErrorMsg}
                </ModelSelectorName>
              ) : (
                <>
                  {selectedModelData?.chefSlug && (
                    <ModelSelectorLogo provider={selectedModelData.chefSlug} />
                  )}
                  <ModelSelectorName>
                    {selectedModelData?.name || selectedModel || "Select model"}
                  </ModelSelectorName>
                </>
              )}
            </ModelSelectorTrigger>
            <ModelSelectorContent>
              <ModelSelectorInput placeholder="Search models..." />
              <ModelSelectorList>
                <ModelSelectorEmpty>No models found.</ModelSelectorEmpty>
                {chefGroups.map((chef) => (
                  <ModelSelectorGroup key={chef} heading={chef}>
                    {models
                      .filter((m) => m.chef === chef)
                      .map((m) => (
                        <ModelSelectorItem
                          key={m.id}
                          onSelect={() => {
                            setUserSelectedModel(m.id);
                            setModelSelectorOpen(false);
                          }}
                          value={m.id}
                        >
                          <ModelSelectorLogo provider={m.chefSlug} />
                          <ModelSelectorName>{m.name}</ModelSelectorName>
                          <ModelSelectorLogoGroup>
                            {m.providers.map((provider) => (
                              <ModelSelectorLogo
                                key={provider}
                                provider={provider}
                              />
                            ))}
                          </ModelSelectorLogoGroup>
                          {selectedModel === m.id ? (
                            <CheckIcon className="ml-auto size-4" />
                          ) : (
                            <div className="ml-auto size-4" />
                          )}
                        </ModelSelectorItem>
                      ))}
                  </ModelSelectorGroup>
                ))}
              </ModelSelectorList>
            </ModelSelectorContent>
          </ModelSelector>
        </div>
      </header>

      {/* Chat Messages - scrollable, content centered */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className={`${contentWidth} py-4 space-y-6`}>
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-500 text-lg">
                Start a conversation with OCI OpenAI
              </div>
              <div className="text-gray-400 text-sm mt-2">
                Ask me anything and I’ll respond using Oracle’s AI models
              </div>
            </div>
          )}

          {messages.map((message: ChatMessage, index: number) => {
            const normalizedParts = normalizeMessageParts(message.parts);
            const textContent =
              getConcatenatedTextFromNormalizedParts(normalizedParts);

            if (!textContent && normalizedParts.length === 0) {
              return null;
            }

            const isLastMessage = index === messages.length - 1;
            const isStreaming =
              isLastMessage &&
              (status === "submitted" || status === "streaming");
            const showActions =
              message.role === "assistant" && textContent && !isStreaming;

            return (
              <div key={`msg-${index}-${message.id ?? message.role}`}>
                <Message from={message.role}>
                  <MessageContent
                    className={
                      message.role === "assistant"
                        ? "bg-white border border-gray-200 rounded-lg px-4 py-3 shadow-sm max-w-full"
                        : undefined
                    }
                  >
                    {normalizedParts.map((part, partIndex) => {
                      if (part.kind === "text") {
                        const text = part.text;

                        if (!text) return null;

                        return (
                          <div key={`text-${partIndex}`}>
                            {renderMarkdownWithCodeBlocks(text)}
                          </div>
                        );
                      }

                      const tool = part.tool;

                      return (
                        <Tool key={`tool-${partIndex}`} defaultOpen>
                          <ToolHeader type={tool.type} state={tool.state} />
                          <ToolContent>
                            {tool.input != null && (
                              <ToolInput input={tool.input} />
                            )}
                            {(tool.output !== undefined || tool.errorText) && (
                              <ToolOutput
                                output={tool.output}
                                errorText={tool.errorText}
                              />
                            )}
                          </ToolContent>
                        </Tool>
                      );
                    })}
                  </MessageContent>
                </Message>
                {showActions && (
                  <MessageActions>
                    <MessageAction
                      onClick={() => {
                        navigator.clipboard.writeText(textContent);
                      }}
                      label="Copy"
                      tooltip="Copy message"
                    >
                      <CopyIcon className="size-3" />
                    </MessageAction>
                  </MessageActions>
                )}
              </div>
            );
          })}

          {/* Optimistic user message when a suggestion was just clicked (hide once real message is in list) */}
          {showOptimisticSuggestion && (
            <div key="pending-suggestion">
              <Message from="user">
                <MessageContent>{pendingSuggestion}</MessageContent>
              </Message>
            </div>
          )}

          {(status === "submitted" ||
            status === "streaming" ||
            pendingSuggestion != null) && (
            <Message from="assistant">
              <MessageContent>{THINKING_INDICATOR}</MessageContent>
            </Message>
          )}
        </div>
      </div>

      {/* Suggestions + Input Form - full width bar, always visible */}
      <div className="sticky bottom-0 z-10 shrink-0 bg-white border-t border-gray-200 shadow-[0_-1px_3px_rgba(0,0,0,0.05)]">
        <div className={contentWidth}>
          {status !== "submitted" &&
            status !== "streaming" &&
            pendingSuggestion == null &&
            !suggestionsLoading && (
              <Suggestions className="pt-4 pb-2">
                {(dynamicSuggestions?.length
                  ? dynamicSuggestions
                  : SUGGESTIONS
                ).map((suggestion) => (
                  <Suggestion
                    key={suggestion}
                    suggestion={suggestion}
                    onClick={handleSuggestionClick}
                  />
                ))}
              </Suggestions>
            )}
          <form onSubmit={handleSubmit} className="py-4 flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                !selectedModel && !modelsLoading
                  ? "Select a model first"
                  : "Type your message here..."
              }
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={status !== "ready" || !selectedModel}
            />
            <button
              type="submit"
              disabled={status !== "ready" || !input.trim() || !selectedModel}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
