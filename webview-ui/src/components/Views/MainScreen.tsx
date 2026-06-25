import TabButton from "../TabButton.tsx";
import { SearchPanel } from "../SearchPanel.tsx";
import { useState, useEffect } from "react";

import { AddNoteModal } from "../NoteModal/AddNoteModal.tsx";
import {
  Search,
  MessageSquare,
  Calendar,
  StickyNote,
  Plus,
  X,
} from "lucide-react";
import { AISummaryPanel } from "../Panels/AISummaryPanel.tsx";
import { MeetingMinutesView } from "../Panels/MeetingMinutesView.tsx";
import { vscode } from "../../utilities/vscodeApi.ts";

type View = "search" | "ai" | "meetings";

interface LLMGroup {
  provider: string;
  models: string[];
}

const staticLLMGroups: LLMGroup[] = [
  {
    provider: "OpenAI",
    models: ["GPT-5.4", "GPT-5.5", "GPT-5.5 Pro"],
  },
  {
    provider: "Gemini",
    models: ["Gemini 3.1 Pro", "Gemini 3.1 Flash", "Gemini 3.5 Flash"],
  },
];

const MainScreen = () => {
  const [currentView, setCurrentView] = useState<View>("search");
  const [showAddNote, setShowAddNote] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState("GPT-5.4");
  const [isLLMDropdownOpen, setIsLLMDropdownOpen] = useState(false);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);

  const llmGroups: LLMGroup[] = [
    ...staticLLMGroups,
    { provider: "Ollama", models: ollamaModels },
  ];

  useEffect(() => {
    vscode.postMessage("getOllamaModels");

    const handleMessage = (event: MessageEvent) => {
      const message = event.data;
      if (message.command === "ollamaModels") {
        console.log("REACT:: Received Ollama Models: ", message.data);
        const models = Array.isArray(message.data)
          ? message.data
          : Array.isArray(message.data?.models)
            ? message.data.models
            : [];
        setOllamaModels(models);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

 

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

  const handleClose = () => {
    vscode.postMessage("close_panel");
  };

  return (
    <div className="h-screen shrink-0 min-w-xs overflow-x-hidden flex flex-col bg-[#1e1e1e] text-[#cccccc]">
      {/* Header — topmost row: icon + title + close button */}
      <div className="h-9 bg-[#252526] border-b border-[#3e3e42] flex items-center justify-between px-3">
        <div className="flex items-center gap-3">
          <StickyNote className="w-4 h-4 text-[#4ec9b0]" />
          <span className="text-sm">Code Notes</span>
        </div>
        {/* Plus button for adding notes */}
        <TabButton
          icon={<Plus className="w-3 h-3" />}
          label=""
          onClick={() => setShowAddNote(true)}
          type="blue"
        />
      </div>

      {/* Tab Bar */}
      <div className="h-9 bg-[#252526] justify-between border-b border-[#3e3e42] flex items-center px-2 gap-1 relative">
        <div className="flex min-w-0">
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
          <div className="relative shrink min-w-0">
            <TabButton
              className="mr-1 max-w-full"
              label={`Pick LLM (${selectedLLM})`}
              onClick={toggleLLMDropdown}
              type="blue"
            />

            {isLLMDropdownOpen && (
              <div className="absolute right-0 mt-1 w-48 max-h-64 overflow-y-auto bg-[#252526] border border-[#3e3e42] rounded shadow-lg z-20">
                {llmGroups.map((group, groupIdx) => (
                  <div key={group.provider}>
                    {groupIdx > 0 && (
                      <div className="border-t border-[#3e3e42]" />
                    )}
                    <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-[#888] font-semibold">
                      {group.provider}
                    </div>
                    {group.models.length > 0 ? (
                      group.models.map((model) => (
                        <button
                          key={`${group.provider}-${model}`}
                          onClick={() => selectLLM(model)}
                          className={`w-full text-left px-3 py-1.5 text-xs hover:bg-[#1a1a1a] ${
                            selectedLLM === model
                              ? "font-semibold text-[#4ec9b0]"
                              : "text-[#cccccc]"
                          }`}
                        >
                          {model}
                        </button>
                      ))
                    ) : (
                      <div className="px-3 py-1.5 text-xs text-[#666] italic">
                        No models available
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Content — all panels stay mounted so their internal state
          (search query/results, chat history, selections) is preserved
          when switching tabs. Inactive panels are hidden via CSS. */}
      <div className="flex-1 overflow-hidden">
        <div className={currentView === "search" ? "h-full" : "hidden"}>
          <SearchPanel />
        </div>
        <div className={currentView === "ai" ? "h-full" : "hidden"}>
          <AISummaryPanel />
        </div>
        <div className={currentView === "meetings" ? "h-full" : "hidden"}>
          <MeetingMinutesView />
        </div>
      </div>

      {/* Add Note Modal */}
      {showAddNote && <AddNoteModal onClose={() => setShowAddNote(false)} />}
    </div>
  );
};

export default MainScreen;