import { useState } from "react";
import {
  Send,
  Bot,
  User,
  ChevronDown,
  ChevronRight,
  FileText,
} from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: Source[];
}

interface Source {
  noteId: string;
  title: string;
  filePath?: string;
  type: string;
}

const mockMessages: Message[] = [
  {
    id: "1",
    role: "user",
    content: "Summarize all authentication-related notes",
    timestamp: "2025-12-07T11:30:00",
  },
  {
    id: "2",
    role: "assistant",
    content:
      "Based on your authentication notes, here's a comprehensive summary:\n\n**Core Implementation:**\nYour authentication system uses JWT tokens with a refresh mechanism. The validateToken function performs three key checks: token expiration, signature validity, and user permissions.\n\n**Security Measures:**\n- Tokens are stored in httpOnly cookies\n- CSRF protection is enabled\n- Rate limiting on auth endpoints\n- OAuth 2.0 integration with PKCE for Google, GitHub, and Microsoft\n\n**Recent Updates:**\nThe database schema was updated to support OAuth integration. Migration 0012_add_oauth.sql adds necessary columns to the users table.\n\n**Action Items from Security Review:**\n- Implement additional rate limiting\n- Review token expiration policies\n- Add monitoring for failed auth attempts",
    timestamp: "2025-12-07T11:30:05",
    sources: [
      {
        noteId: "1",
        title: "Authentication Flow Implementation",
        filePath: "src/auth/validator.ts",
        type: "function",
      },
      {
        noteId: "2",
        title: "Database Schema Update",
        filePath: "migrations/0012_add_oauth.sql",
        type: "file",
      },
      { noteId: "3", title: "OAuth Integration Notes", type: "feature" },
      { noteId: "4", title: "Security Review Meeting", type: "meeting" },
    ],
  },
];

export function AISummaryPanel() {
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages([...messages, userMessage]);
    setInput("");
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "This is a simulated AI response. In a real implementation, this would use your AI model to summarize notes based on the query.",
        timestamp: new Date().toISOString(),
        sources: [],
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* Header */}
      <div className="h-10 bg-[#252526] border-b border-[#3e3e42] flex items-center px-3">
        <Bot className="w-3.5 h-3.5 text-[#4ec9b0] mr-2" />
        <h2 className="text-xs text-[#ffffff]">AI Summary</h2>
        {/*
            TODO:
              add selection for llm 
              check how to get models download by ollama 
              + hugging face 
        */}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-[#6a6a6a] px-3">
            <div className="text-center">
              <Bot className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-xs mb-2">Ask me about your notes</p>
              <p className="text-[10px] leading-relaxed mb-3">
                I can summarize notes, find connections, and provide insights.
              </p>
              <div className="text-left">
                <div className="text-xs p-2 bg-[#252526] border border-[#3e3e42] rounded">
                  <div className="text-[#4ec9b0] mb-1 text-[10px]">
                    Examples:
                  </div>
                  <div className="text-[#6a6a6a] space-y-0.5 text-[10px]">
                    <div>• Summarize auth notes</div>
                    <div>• Recent meeting decisions</div>
                    <div>• Critical security issues</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isTyping && (
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
        )}
      </div>

      {/* Input */}
      <div className="border-t border-[#3e3e42] bg-[#252526] p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Ask about your notes..."
            className="flex-1 px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="px-4 py-2 bg-[#0e639c] hover:bg-[#1177bb] disabled:bg-[#3e3e42] disabled:text-[#6a6a6a] text-[#ffffff] rounded transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  return (
    <div className="flex items-start gap-3">
      {/* Avatar */}
      <div
        className={`
        w-6 h-6 rounded flex items-center justify-center flex-shrink-0
        ${message.role === "assistant" ? "bg-[#4ec9b0]/20" : "bg-[#0e639c]/20"}
      `}
      >
        {message.role === "assistant" ? (
          <Bot className="w-4 h-4 text-[#4ec9b0]" />
        ) : (
          <User className="w-4 h-4 text-[#0e639c]" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div
          className={`
          inline-block px-3 py-2 rounded max-w-full
          ${
            message.role === "assistant"
              ? "bg-[#252526] border border-[#3e3e42]"
              : "bg-[#0e639c]/20 border border-[#0e639c]/30"
          }
        `}
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
