import { useState, useEffect } from "react";
import { vscode } from "../../../utilities/vscodeApi";
import type { Message } from "./types";
import { ChatMessageList } from "./ChatMessageList";
import { ChatInput } from "./ChatInput";

/**
 * AISummaryPanel — main entry point.
 * Owns all chat state and the VSCode ↔ extension message bridge.
 */
export function AISummaryPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  // ── VSCode extension → webview messages ──────────────────────────────────
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const { command, data } = event.data ?? {};

      if (command === "llm_response") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "assistant",
            content: data?.response ?? "",
            timestamp: new Date().toISOString(),
            sources: data?.sources ?? [],
          },
        ]);
        setIsTyping(false);
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
      <ChatMessageList messages={messages} isTyping={isTyping} />
      <ChatInput
        input={input}
        isTyping={isTyping}
        onChange={setInput}
        onSend={handleSend}
      />
    </div>
  );
}
