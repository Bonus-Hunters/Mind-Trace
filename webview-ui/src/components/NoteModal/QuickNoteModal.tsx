import { useState } from "react";
import { X, Send } from "lucide-react";
import { vscode } from "../../utilities/vscodeApi.ts";

interface QuickNoteModalProps {
  functionName: string;
  fileName: string;
  lineNumber: number;
  onClose: () => void;
}

export function QuickNoteModal({
  functionName,
  fileName,
  lineNumber,
  onClose,
}: QuickNoteModalProps) {
  const [noteContent, setNoteContent] = useState("");
  const [metadata, setMetadata] = useState("");

  const canSend = noteContent.trim().length > 0;

  const handleSend = () => {
    if (!canSend) return;
    vscode.postMessage("saveQuickNote", {
      noteContent: noteContent.trim(),
      metadata: metadata.trim(),
      functionName,
      fileName,
      lineNumber,
    });
    onClose();
  };

  // Enter submits (Shift+Enter inserts a newline), mirroring ChatInput.
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#252526] border border-[#3e3e42] rounded shadow-2xl w-[420px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-[#3e3e42]">
          <h2 className="text-sm text-[#ffffff]">Add Note</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#2a2d2e] rounded transition-colors"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>

        {/* Content */}
        <div className="p-3 space-y-3">
          {/* Captured code context */}
          <div className="text-[11px] text-[#888] font-mono truncate">
            <span className="text-[#4ec9b0]">{functionName || "(no name)"}</span>
            {"  "}·{"  "}
            {fileName}:{lineNumber}
          </div>

          {/* Note content (mandatory) */}
          <textarea
            autoFocus
            value={noteContent}
            onChange={(e) => setNoteContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Note content..."
            rows={3}
            className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors resize-none font-mono"
          />

          {/* Metadata (optional) */}
          <input
            type="text"
            value={metadata}
            onChange={(e) => setMetadata(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="metadata, comma, separated (optional)"
            className="w-full px-3 py-1.5 bg-[#3c3c3c] border border-[#3e3e42] rounded text-[11px] text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-3 border-t border-[#3e3e42]">
          <button
            onClick={handleSend}
            disabled={!canSend}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs bg-[#0e639c] hover:bg-[#1177bb] text-[#ffffff] rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-3 h-3" />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
