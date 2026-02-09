import { useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  File,
  FunctionSquare,
  Tag,
  Calendar,
  Folder,
} from "lucide-react";
import type { Note } from "./Panels/MainPanel";

interface TreeViewProps {
  notes: Note[];
  selectedNoteId?: string;
  onSelectNote: (note: Note) => void;
}

export function TreeView({
  notes,
  selectedNoteId,
  onSelectNote,
}: TreeViewProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["files", "functions", "features", "meetings"]),
  );
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const toggleFile = (file: string) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(file)) {
      newExpanded.delete(file);
    } else {
      newExpanded.add(file);
    }
    setExpandedFiles(newExpanded);
  };

  // Group notes by file for file/function hierarchy
  const notesByFile = notes.reduce(
    (acc, note) => {
      if (note.filePath) {
        if (!acc[note.filePath]) {
          acc[note.filePath] = [];
        }
        acc[note.filePath].push(note);
      }
      return acc;
    },
    {} as Record<string, Note[]>,
  );

  const fileNotes = notes.filter((n) => n.type === "file");
  const functionNotes = notes.filter((n) => n.type === "function");
  const featureNotes = notes.filter((n) => n.type === "feature");
  const meetingNotes = notes.filter((n) => n.type === "meeting");

  return (
    <div className="p-2 text-xs font-mono">
      {/* Files & Functions Section */}
      <Section
        title="FILES & FUNCTIONS"
        icon={<Folder className="w-4 h-4" />}
        expanded={expandedSections.has("files")}
        onToggle={() => toggleSection("files")}
        count={Object.keys(notesByFile).length}
      >
        {Object.entries(notesByFile).map(([filePath, fileNotes]) => (
          <div key={filePath}>
            <TreeItem
              icon={<File className="w-4 h-4 text-[#519aba]" />}
              label={filePath.split("/").pop() || filePath}
              sublabel={filePath}
              expanded={expandedFiles.has(filePath)}
              onToggle={() => toggleFile(filePath)}
              hasChildren={fileNotes.length > 0}
              indent={1}
            />
            {expandedFiles.has(filePath) && (
              <div className="ml-2">
                {fileNotes.map((note) => (
                  <TreeItem
                    key={note.id}
                    icon={
                      note.type === "function" ? (
                        <FunctionSquare className="w-4 h-4 text-[#dcdcaa]" />
                      ) : (
                        <File className="w-4 h-4 text-[#519aba]" />
                      )
                    }
                    label={note.functionName || note.title}
                    sublabel={
                      note.lineNumber ? `Line ${note.lineNumber}` : undefined
                    }
                    selected={note.id === selectedNoteId}
                    onClick={() => onSelectNote(note)}
                    indent={2}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </Section>

      {/* Features Section */}
      <Section
        title="FEATURES & TAGS"
        icon={<Tag className="w-4 h-4" />}
        expanded={expandedSections.has("features")}
        onToggle={() => toggleSection("features")}
        count={featureNotes.length}
      >
        {featureNotes.map((note) => (
          <TreeItem
            key={note.id}
            icon={<Tag className="w-4 h-4 text-[#c586c0]" />}
            label={note.title}
            selected={note.id === selectedNoteId}
            onClick={() => onSelectNote(note)}
            indent={1}
          />
        ))}
      </Section>

      {/* Meeting Minutes Section */}
      <Section
        title="MEETING MINUTES"
        icon={<Calendar className="w-4 h-4" />}
        expanded={expandedSections.has("meetings")}
        onToggle={() => toggleSection("meetings")}
        count={meetingNotes.length}
      >
        {meetingNotes.map((note) => (
          <TreeItem
            key={note.id}
            icon={<Calendar className="w-4 h-4 text-[#4ec9b0]" />}
            label={note.title}
            sublabel={new Date(note.timestamp).toLocaleDateString()}
            selected={note.id === selectedNoteId}
            onClick={() => onSelectNote(note)}
            indent={1}
          />
        ))}
      </Section>
    </div>
  );
}

function Section({
  title,
  icon,
  expanded,
  onToggle,
  count,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-2">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-1 px-1 py-1 hover:bg-[#2a2d2e] rounded transition-colors text-[#cccccc]"
      >
        {expanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
        {icon}
        <span className="flex-1 text-left uppercase tracking-wide">
          {title}
        </span>
        <span className="text-[#6a6a6a]">{count}</span>
      </button>
      {expanded && <div className="mt-1">{children}</div>}
    </div>
  );
}

function TreeItem({
  icon,
  label,
  sublabel,
  selected,
  expanded,
  hasChildren,
  onToggle,
  onClick,
  indent = 0,
}: {
  icon: React.ReactNode;
  label: string;
  sublabel?: string;
  selected?: boolean;
  expanded?: boolean;
  hasChildren?: boolean;
  onToggle?: () => void;
  onClick?: () => void;
  indent?: number;
}) {
  return (
    <button
      onClick={hasChildren ? onToggle : onClick}
      className={`
        w-full flex items-center gap-1 px-1 py-1 rounded transition-colors text-left
        ${selected ? "bg-[#37373d] text-[#ffffff]" : "hover:bg-[#2a2d2e] text-[#cccccc]"}
      `}
      style={{ paddingLeft: `${indent * 12 + 4}px` }}
    >
      {hasChildren &&
        (expanded ? (
          <ChevronDown className="w-3 h-3 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3 h-3 flex-shrink-0" />
        ))}
      <span className="flex-shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="truncate">{label}</div>
        {sublabel && (
          <div className="text-[10px] text-[#6a6a6a] truncate">{sublabel}</div>
        )}
      </div>
    </button>
  );
}
