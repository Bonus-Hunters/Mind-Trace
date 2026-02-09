import { useState } from "react";
import { X, FileText, FunctionSquare, Tag, Calendar } from "lucide-react";

interface AddNoteModalProps {
  onClose: () => void;
}

type NoteType = "function" | "file" | "feature" | "meeting";

export function AddNoteModal({ onClose }: AddNoteModalProps) {
  const [noteType, setNoteType] = useState<NoteType>("function");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [filePath, setFilePath] = useState("");
  const [functionName, setFunctionName] = useState("");
  const [lineNumber, setLineNumber] = useState("");
  const [tags, setTags] = useState("");

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#252526] border border-[#3e3e42] rounded shadow-2xl w-[600px] max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#3e3e42]">
          <h2 className="text-sm text-[#ffffff]">Add New Note</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#2a2d2e] rounded transition-colors"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {/* Note Type Selector */}
          <div>
            <label className="block text-xs text-[#cccccc] mb-2 font-mono">
              Note Type
            </label>
            <div className="grid grid-cols-4 gap-2">
              <TypeButton
                icon={<FunctionSquare className="w-4 h-4" />}
                label="Function"
                selected={noteType === "function"}
                onClick={() => setNoteType("function")}
              />
              <TypeButton
                icon={<FileText className="w-4 h-4" />}
                label="File"
                selected={noteType === "file"}
                onClick={() => setNoteType("file")}
              />
              <TypeButton
                icon={<Tag className="w-4 h-4" />}
                label="Feature"
                selected={noteType === "feature"}
                onClick={() => setNoteType("feature")}
              />
              <TypeButton
                icon={<Calendar className="w-4 h-4" />}
                label="Meeting"
                selected={noteType === "meeting"}
                onClick={() => setNoteType("meeting")}
              />
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs text-[#cccccc] mb-2 font-mono">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter note title..."
              className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs text-[#cccccc] mb-2 font-mono">
              Description *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter note description (supports markdown)..."
              rows={6}
              className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors resize-none font-mono"
            />
          </div>

          {/* Optional Fields */}
          {(noteType === "function" || noteType === "file") && (
            <>
              <div>
                <label className="block text-xs text-[#cccccc] mb-2 font-mono">
                  File Path {noteType === "file" && "*"}
                </label>
                <input
                  type="text"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                  placeholder="src/components/Example.tsx"
                  className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
                />
              </div>

              {noteType === "function" && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-[#cccccc] mb-2 font-mono">
                      Function Name
                    </label>
                    <input
                      type="text"
                      value={functionName}
                      onChange={(e) => setFunctionName(e.target.value)}
                      placeholder="handleSubmit"
                      className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-[#cccccc] mb-2 font-mono">
                      Line Number
                    </label>
                    <input
                      type="text"
                      value={lineNumber}
                      onChange={(e) => setLineNumber(e.target.value)}
                      placeholder="142"
                      className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
                    />
                  </div>
                </div>
              )}
            </>
          )}

          {/* Tags */}
          <div>
            <label className="block text-xs text-[#cccccc] mb-2 font-mono">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="auth, security, critical"
              className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-[#3e3e42]">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs bg-[#3c3c3c] hover:bg-[#4a4a4a] text-[#cccccc] rounded transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs bg-[#0e639c] hover:bg-[#1177bb] text-[#ffffff] rounded transition-colors"
          >
            Save Note
          </button>
        </div>
      </div>
    </div>
  );
}

function TypeButton({
  icon,
  label,
  selected,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        flex flex-col items-center gap-1 p-3 rounded border transition-colors
        ${
          selected
            ? "bg-[#0e639c] border-[#007acc] text-[#ffffff]"
            : "bg-[#3c3c3c] border-[#3e3e42] text-[#cccccc] hover:bg-[#4a4a4a]"
        }
      `}
    >
      {icon}
      <span className="text-xs">{label}</span>
    </button>
  );
}
