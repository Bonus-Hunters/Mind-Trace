import { Bot, User } from "lucide-react";
import type { Message } from "./types";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isAssistant = message.role === "assistant";

  return (
    <div className="flex items-start gap-3">
      {/* Avatar */}
      <div
        className={`w-6 h-6 rounded flex items-center justify-center flex-shrink-0 ${
          isAssistant ? "bg-[#4ec9b0]/20" : "bg-[#0e639c]/20"
        }`}
      >
        {isAssistant ? (
          <Bot className="w-4 h-4 text-[#4ec9b0]" />
        ) : (
          <User className="w-4 h-4 text-[#0e639c]" />
        )}
      </div>

      {/* Bubble */}
      <div className="flex-1 min-w-0">
        <div
          className={`inline-block px-3 py-2 rounded max-w-full ${
            isAssistant
              ? "bg-[#252526] border border-[#3e3e42]"
              : "bg-[#0e639c]/20 border border-[#0e639c]/30"
          }`}
        >
          <div className="text-xs text-[#cccccc] leading-relaxed whitespace-pre-wrap font-mono">
            {message.content}
          </div>
        </div>

        <div className="text-[10px] text-[#6a6a6a] mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
