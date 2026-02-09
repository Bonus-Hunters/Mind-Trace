import { useState } from "react";
import { TreeView } from "../TreeView";
import { NoteDetails } from "../NoteDetails";

export interface Note {
  id: string;
  title: string;
  content: string;
  type: "function" | "file" | "feature" | "meeting";
  filePath?: string;
  functionName?: string;
  lineNumber?: number;
  timestamp: string;
  tags: string[];
}

const mockNotes: Note[] = [
  {
    id: "1",
    title: "Authentication Flow Implementation",
    content:
      "## Implementation Notes\n\nUsed JWT tokens with refresh mechanism. The `validateToken` function checks:\n- Token expiration\n- Signature validity\n- User permissions\n\n**Security considerations:**\n- Tokens stored in httpOnly cookies\n- CSRF protection enabled\n- Rate limiting on auth endpoints",
    type: "function",
    filePath: "src/auth/validator.ts",
    functionName: "validateToken",
    lineNumber: 45,
    timestamp: "2025-12-07T10:30:00",
    tags: ["auth", "security", "critical"],
  },
  {
    id: "2",
    title: "Database Schema Update",
    content:
      "Added new columns to users table for OAuth integration. Remember to run migrations before deploying.",
    type: "file",
    filePath: "migrations/0012_add_oauth.sql",
    lineNumber: 1,
    timestamp: "2025-12-06T14:22:00",
    tags: ["database", "migration"],
  },
  {
    id: "3",
    title: "Dark Mode Feature",
    content:
      "## Dark Mode Implementation\n\nUsing CSS variables for theme switching. Need to:\n1. Add theme toggle in settings\n2. Persist preference in localStorage\n3. Respect system preference by default",
    type: "feature",
    timestamp: "2025-12-05T09:15:00",
    tags: ["ui", "feature", "enhancement"],
  },
  {
    id: "4",
    title: "Sprint Planning - Q1 2026",
    content:
      "## Meeting Notes\n\n**Attendees:** Dev team, PM, Design\n\n**Decisions:**\n- Focus on performance improvements\n- API v2 migration timeline\n- New dashboard design approved\n\n**Action items:**\n- @john: Create performance benchmarks\n- @sarah: Draft API migration guide",
    type: "meeting",
    timestamp: "2025-12-04T15:00:00",
    tags: ["planning", "sprint", "q1-2026"],
  },
];

export function MainPanel() {
  const [selectedNote, setSelectedNote] = useState<Note | null>(mockNotes[0]);

  return (
    <div className="flex h-full">
      {/* Left Sidebar - Tree View */}
      <div className="w-80 border-r border-[#3e3e42] bg-[#252526] overflow-auto">
        <TreeView
          notes={mockNotes}
          selectedNoteId={selectedNote?.id}
          onSelectNote={setSelectedNote}
        />
      </div>

      {/* Right Panel - Note Details */}
      <div className="flex-1 overflow-auto">
        {selectedNote ? (
          <NoteDetails note={selectedNote} />
        ) : (
          <div className="flex items-center justify-center h-full text-[#6a6a6a]">
            <div className="text-center">
              <p className="text-sm">No note selected</p>
              <p className="text-xs mt-1">Select a note from the tree view</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
