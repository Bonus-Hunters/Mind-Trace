import "./App.css";
import { useState } from "react";
import TabButton from "./components/TabButton.tsx";

import {
  Search,
  MessageSquare,
  Calendar,
  StickyNote,
  Plus,
} from "lucide-react";

type View = "search" | "ai" | "meetings";

function App() {
  const [currentView, setCurrentView] = useState<View>("search");
  // const [showAddNote, setShowAddNote] = useState(false);

  return (
    <div
      className="h-screen flex flex-col bg-[#1e1e1e] text-[#cccccc]"
      style={{
        width: "33.333vw",
        minWidth: "280px",
        maxWidth: "500px",
      }}
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <StickyNote className="w-4 h-4 text-[#4ec9b0]" />
          <span className="text-sm">Code Notes</span>
          <button
            // onClick={() => setShowAddNote(true)}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-[#0e639c] hover:bg-[#1177bb] rounded transition-colors"
          >
            <Plus className="w-3 h-3" />
            New Note
          </button>
        </div>
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
    </div>
  );
}

export default App;
