import { useState, useEffect, memo } from "react";
import { vscode } from "../../../utilities/vscodeApi";
import type { Message } from "./types";
import type { ResolvedFileMap } from "./fileLinkUtils";
import { extractFileNames } from "./fileLinkUtils";
import { ChatMessageList } from "./ChatMessageList";
import { ChatInput } from "./ChatInput";

/**
 * AISummaryPanel — main entry point.
 * Owns all chat state and the VSCode ↔ extension message bridge.
 */
export const AISummaryPanel = memo(function AISummaryPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [resolvedByMessage, setResolvedByMessage] = useState<
    Record<string, ResolvedFileMap>
  >({});

  // ── VSCode extension → webview messages ──────────────────────────────────
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const { command, data } = event.data ?? {};

      if (command === "llm_response") {
        const id = Date.now().toString();
        const content: string = data?.response ?? "";

        setMessages((prev) => [
          ...prev,
          {
            id,
            role: "assistant",
            content,
            timestamp: new Date().toISOString(),
            sources: data?.sources ?? [],
          },
        ]);
        setIsTyping(false);

        // Ask the extension to resolve any filenames mentioned in the reply so
        // they can be rendered as clickable links.
        const fileNames = extractFileNames(content);
        if (fileNames.length > 0) {
          vscode.postMessage("resolveFileNames", { messageId: id, fileNames });
        }
      }

      if (command === "fileNamesResolved") {
        setResolvedByMessage((prev) => ({
          ...prev,
          [data?.messageId]: data?.resolved ?? {},
        }));
      }

      if (command === "llm_error") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "assistant",
            content: `⚠️ Error: ${data?.error ?? "Something went wrong."}`,
            timestamp: new Date().toISOString(),
          },
        ]);
        setIsTyping(false);
      }
    };

    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

  // ── Send handler ─────────────────────────────────────────────────────────
  const handleSend = () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Forward query to the VS Code extension → backend
    vscode.postMessage("send_query_to_llm", { query: input });

    setInput("");
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      <ChatMessageList
        messages={messages}
        isTyping={isTyping}
        resolvedByMessage={resolvedByMessage}
      />
      <ChatInput
        input={input}
        isTyping={isTyping}
        onChange={setInput}
        onSend={handleSend}
      />
    </div>
  );
});
