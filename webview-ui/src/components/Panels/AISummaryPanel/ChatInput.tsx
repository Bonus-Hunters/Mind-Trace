import { Send } from "lucide-react";

interface Props {
  input: string;
  isTyping: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
}

/** Text input + send button row at the bottom of the chat panel. */
export function ChatInput({ input, isTyping, onChange, onSend }: Props) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="border-t border-[#3e3e42] bg-[#252526] p-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          disabled={isTyping}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your notes..."
          className="flex-1 px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          onClick={onSend}
          disabled={!input.trim() || isTyping}
          className="px-4 py-2 bg-[#0e639c] hover:bg-[#1177bb] disabled:bg-[#3e3e42] disabled:text-[#6a6a6a] text-[#ffffff] rounded transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
