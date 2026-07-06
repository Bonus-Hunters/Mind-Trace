import { useEffect, useRef } from "react";
import type { Message } from "./types";
import type { ResolvedFileMap } from "./fileLinkUtils";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { ChatEmptyState } from "./ChatEmptyState";

interface Props {
  messages: Message[];
  isTyping: boolean;
  resolvedByMessage: Record<string, ResolvedFileMap>;
}

/** Scrollable area that renders the full message history. */
export function ChatMessageList({
  messages,
  isTyping,
  resolvedByMessage,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom whenever a new message arrives or typing starts
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div className="flex-1 overflow-auto p-3 space-y-3">
      {messages.length === 0 && !isTyping && <ChatEmptyState />}

      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          resolved={resolvedByMessage[message.id]}
        />
      ))}

      {isTyping && <TypingIndicator />}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
}
