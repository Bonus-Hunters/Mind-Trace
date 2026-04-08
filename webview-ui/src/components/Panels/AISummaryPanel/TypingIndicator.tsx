import { Bot } from "lucide-react";

/** Three bouncing dots shown while the LLM is processing a response. */
export function TypingIndicator() {
  return (
    <div className="flex items-start gap-3">
      <div className="w-6 h-6 rounded bg-[#4ec9b0]/20 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-[#4ec9b0]" />
      </div>
      <div className="flex-1">
        <div className="inline-block px-3 py-2 bg-[#252526] border border-[#3e3e42] rounded">
          <div className="flex gap-1">
            <div
              className="w-2 h-2 bg-[#6a6a6a] rounded-full animate-bounce"
              style={{ animationDelay: "0ms" }}
            />
            <div
              className="w-2 h-2 bg-[#6a6a6a] rounded-full animate-bounce"
              style={{ animationDelay: "150ms" }}
            />
            <div
              className="w-2 h-2 bg-[#6a6a6a] rounded-full animate-bounce"
              style={{ animationDelay: "300ms" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
