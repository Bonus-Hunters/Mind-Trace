import TabButton from "../TabButton.tsx";
import { SearchPanel } from "../SearchPanel.tsx";
import { useState } from "react";

import { AddNoteModal } from "../NoteModal/AddNoteModal.tsx";
import {
  Search,
  MessageSquare,
  Calendar,
  StickyNote,
  Plus,
} from "lucide-react";
import { AISummaryPanel } from "../Panels/AISummaryPanel.tsx";
import { MeetingMinutesView } from "../Panels/MeetingMinutesView.tsx";
import { vscode } from "../../utilities/vscodeApi.ts";

type View = "search" | "ai" | "meetings";

const MainScreen = () => {
  const [currentView, setCurrentView] = useState<View>("search");
  const [showAddNote, setShowAddNote] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState("GPT-4");
  const [isLLMDropdownOpen, setIsLLMDropdownOpen] = useState(false);

  const llmOptions = ["GPT-4", "GPT-4o", "Llama 3", "Mistral", "Custom"];

  const toggleLLMDropdown = () => {
    setIsLLMDropdownOpen((prev) => !prev);
  };

  const selectLLM = (llm: string) => {
    if (llm !== selectedLLM) {
      // TODO: change lllm used in backend
      vscode.postMessage("changeLLM", {
        llm: llm,
      });
      setSelectedLLM(llm);
    }
    setIsLLMDropdownOpen(false);
  };

  return (
    <div className="h-screen shrink-0 min-w-xs overflow-x-hidden flex flex-col bg-[#1e1e1e] text-[#cccccc]">
      {/* Header */}
      <div className="h-9 bg-[#252526] border-b border-[#3e3e42] flex items-center justify-between px-3">
        <div className="flex items-center gap-3">
          <StickyNote className="w-4 h-4 text-[#4ec9b0]" />
          <span className="text-sm">Code Notes</span>
        </div>
        {/* Plus butnton for adding notes */}
        <TabButton
          icon={<Plus className="w-3 h-3" />}
          label=""
          onClick={() => setShowAddNote(true)}
          type="blue"
        />
      </div>

      {/* Tab Bar */}
      <div className="h-9 bg-[#252526] justify-between border-b border-[#3e3e42] flex items-center px-2 gap-1 relative">
        <div className="flex">
          <TabButton
            icon={<Search className="w-4 h-4" />}
            label="Search"
            active={currentView === "search"}
            onClick={() => setCurrentView("search")}
            type="black"
          />
          <TabButton
            icon={<MessageSquare className="w-4 h-4" />}
            label="Query"
            active={currentView === "ai"}
            onClick={() => setCurrentView("ai")}
            type="black"
          />
          <TabButton
            icon={<Calendar className="w-4 h-4" />}
            label="Meetings"
            active={currentView === "meetings"}
            onClick={() => setCurrentView("meetings")}
            type="black"
          />
        </div>

        {/*
            TODO:
              add selection for llm 
              check how to get models download by ollama 
              + hugging face 
        */}
        {currentView == "ai" && (
          <div className="relative">
            <TabButton
              className="mr-1"
              label={`Pick LLM (${selectedLLM})`}
              onClick={toggleLLMDropdown}
              type="blue"
            />

            {isLLMDropdownOpen && (
              <div className="absolute right-0 mt-1 w-36 bg-[#252526] border border-[#3e3e42] rounded shadow-lg z-20">
                {llmOptions.map((option) => (
                  <button
                    key={option}
                    onClick={() => selectLLM(option)}
                    className={`w-full text-left px-3 py-2 text-xs hover:bg-[#1a1a1a] ${
                      selectedLLM === option
                        ? "font-semibold text-[#4ec9b0]"
                        : "text-[#cccccc]"
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
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
};

export default MainScreen;
