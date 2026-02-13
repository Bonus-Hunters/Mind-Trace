import "./App.css";
import { useState } from "react";
import TabButton from "./components/TabButton.tsx";
import { SearchPanel } from "./components/SearchPanel.tsx";
import { AddNoteModal } from "./components/NoteModal/AddNoteModal.tsx";
import {
  Search,
  MessageSquare,
  Calendar,
  StickyNote,
  Plus,
} from "lucide-react";
import { AISummaryPanel } from "./components/Panels/AISummaryPanel.tsx";
import { MeetingMinutesView } from "./components/Panels/MeetingMinutesView.tsx";

type View = "search" | "ai" | "meetings";

function App() {
  const [currentView, setCurrentView] = useState<View>("search");
  const [showAddNote, setShowAddNote] = useState(false);

  return (
    <div className="h-screen shrink-0 min-w-xs overflow-x-hidden flex flex-col bg-[#1e1e1e] text-[#cccccc]">
      {/* Header */}
      <div className="h-9 bg-[#252526] border-b border-[#3e3e42] flex items-center justify-between px-3">
        <div className="flex items-center gap-3">
          <StickyNote className="w-4 h-4 text-[#4ec9b0]" />
          <span className="text-sm">Code Notes</span>
        </div>
        <button
          onClick={() => {
            setShowAddNote(true);
          }}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-[#0e639c] hover:bg-[#1177bb] rounded transition-colors"
        >
          <Plus className="w-3 h-3" />
        </button>
      </div>

      {/* Tab Bar */}
      <div className="h-9 bg-[#252526] border-b border-[#3e3e42] flex items-center px-2 gap-1">
        <TabButton
          icon={<Search className="w-4 h-4" />}
          label="Search"
          active={currentView === "search"}
          onClick={() => setCurrentView("search")}
        />
        <TabButton
          icon={<MessageSquare className="w-4 h-4" />}
          label="AI Summary"
          active={currentView === "ai"}
          onClick={() => setCurrentView("ai")}
        />
        <TabButton
          icon={<Calendar className="w-4 h-4" />}
          label="Meetings"
          active={currentView === "meetings"}
          onClick={() => setCurrentView("meetings")}
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {currentView === "search" && <SearchPanel />}
        {currentView === "ai" && <AISummaryPanel />}
        {currentView === "meetings" && <MeetingMinutesView />}
      </div>

      {/* Add Note Modal */}
      {showAddNote && <AddNoteModal onClose={() => setShowAddNote(false)} />}
    </div>
  );
}

export default App;
