import { Edit2, Trash2, FileText, Hash, Clock, MapPin } from "lucide-react";
import type { Note } from "./Panels/MainPanel.tsx";

interface NoteDetailsProps {
  note: Note;
}

export function NoteDetails({ note }: NoteDetailsProps) {
  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* Header */}
      <div className="border-b border-[#3e3e42] bg-[#252526] p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-base text-[#ffffff] mb-2">{note.title}</h2>
            <div className="flex flex-wrap gap-3 text-xs text-[#cccccc]">
              {note.filePath && (
                <div className="flex items-center gap-1">
                  <FileText className="w-3 h-3 text-[#6a6a6a]" />
                  <span className="font-mono">{note.filePath}</span>
                </div>
              )}
              {note.lineNumber && (
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-[#6a6a6a]" />
                  <span className="font-mono">Line {note.lineNumber}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-[#6a6a6a]" />
                <span>{new Date(note.timestamp).toLocaleString()}</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="p-1.5 hover:bg-[#2a2d2e] rounded transition-colors">
              <Edit2 className="w-4 h-4 text-[#cccccc]" />
            </button>
            <button className="p-1.5 hover:bg-[#2a2d2e] rounded transition-colors">
              <Trash2 className="w-4 h-4 text-[#f48771]" />
            </button>
          </div>
        </div>

        {/* Tags */}
        {note.tags.length > 0 && (
          <div className="flex items-center gap-2 mt-3">
            <Hash className="w-3 h-3 text-[#6a6a6a]" />
            <div className="flex flex-wrap gap-1">
              {note.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-[#1e1e1e] border border-[#3e3e42] rounded text-xs text-[#4ec9b0] font-mono"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Function Name if applicable */}
        {note.functionName && (
          <div className="mt-3 p-2 bg-[#1e1e1e] border border-[#3e3e42] rounded">
            <div className="text-xs text-[#6a6a6a] mb-1">Function</div>
            <code className="text-xs text-[#dcdcaa] font-mono">
              {note.functionName}()
            </code>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="prose prose-invert prose-sm max-w-none">
          <MarkdownContent content={note.content} />
        </div>
      </div>
    </div>
  );
}

function MarkdownContent({ content }: { content: string }) {
  // Simple markdown parser for demo
  const lines = content.split("\n");

  return (
    <div className="space-y-2 font-mono text-xs">
      {lines.map((line, i) => {
        // Headers
        if (line.startsWith("## ")) {
          return (
            <h2 key={i} className="text-sm text-[#4ec9b0] mt-4 mb-2">
              {line.slice(3)}
            </h2>
          );
        }
        if (line.startsWith("# ")) {
          return (
            <h1 key={i} className="text-base text-[#4ec9b0] mt-4 mb-2">
              {line.slice(2)}
            </h1>
          );
        }
        // Bold
        if (line.startsWith("**") && line.endsWith("**")) {
          return (
            <p key={i} className="text-[#ffffff]">
              {line.slice(2, -2)}
            </p>
          );
        }
        // List items
        if (line.startsWith("- ")) {
          return (
            <li key={i} className="ml-4 text-[#cccccc]">
              {line.slice(2)}
            </li>
          );
        }
        // Numbered lists
        if (/^\d+\.\s/.test(line)) {
          return (
            <li key={i} className="ml-4 text-[#cccccc]">
              {line.replace(/^\d+\.\s/, "")}
            </li>
          );
        }
        // Code blocks or regular text
        if (line.trim()) {
          return (
            <p key={i} className="text-[#cccccc] leading-relaxed">
              {line}
            </p>
          );
        }
        return <div key={i} className="h-2" />;
      })}
    </div>
  );
}
