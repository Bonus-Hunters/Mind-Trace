import { useState } from "react";
import { X, FunctionSquare, Calendar } from "lucide-react";
import MeetingContent from "./MeetingContent";
import { TypeButton } from "./TypeButtons";
import { vscode } from "../../utilities/vscodeApi.ts";
import NoteContent from "./NoteContent";

interface AddNoteModalProps {
  onClose: () => void;
}

type NoteType = "note" | "meeting";

export function AddNoteModal({ onClose }: AddNoteModalProps) {
  // Note-specific fields
  const [noteType, setNoteType] = useState<NoteType>("note");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [filePath, setFilePath] = useState("");
  const [functionName, setFunctionName] = useState("");
  const [lineNumber, setLineNumber] = useState("");
  const [tags, setTags] = useState("");

  // Meeting-specific fields
  const [meetingDate, setMeetingDate] = useState("");
  const [language, setLanguage] = useState("en");
  const [audioFile, setAudioFile] = useState(null);
  const [projectName, setProjectName] = useState("");

  const closeModal = () => {
    vscode.postMessage("closeAddNoteModal", {
      audioFile: audioFile,
    });
    onClose();
  };

  const handleSave = () => {
    vscode.postMessage("saveNote", {
      noteType: noteType,
      title: title,
      description: description,
      filePath: filePath,
      functionName: functionName,
      lineNumber: lineNumber,
      tags: tags,
      meetingDate: meetingDate,
      language: language,
      audioFile: audioFile,
      projectName: projectName,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#252526] border border-[#3e3e42] rounded shadow-2xl w-[550px] h-[550px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#3e3e42]">
          <h2 className="text-sm text-[#ffffff]">
            {noteType === "meeting" ? "Add New Meeting" : "Add New Note"}
          </h2>
          <button
            onClick={closeModal}
            className="p-1 hover:bg-[#2a2d2e] rounded transition-colors"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {/* Note Type Selector */}
          <div className="justify-center">
            <label className="block text-xs text-[#cccccc] mb-2 font-mono">
              Select Note Type
            </label>
            <div className="grid grid-cols-2 gap-5">
              <TypeButton
                icon={<FunctionSquare className="w-4 h-4" />}
                label="Note"
                selected={noteType === "note"}
                onClick={() => setNoteType("note")}
              />

              <TypeButton
                icon={<Calendar className="w-4 h-4" />}
                label="Meeting"
                selected={noteType === "meeting"}
                onClick={() => setNoteType("meeting")}
              />
            </div>
          </div>

          {/* Meeting-specific fields */}
          {noteType === "meeting" ? (
            <MeetingContent
              title={title}
              meetingDate={meetingDate}
              language={language}
              tags={tags}
              audioFile={audioFile}
              setTitle={setTitle}
              setMeetingDate={setMeetingDate}
              setLanguage={setLanguage}
              setTags={setTags}
              setAudioFile={setAudioFile}
              setProjectName={setProjectName}
              projectName={projectName}
            />
          ) : (
            <NoteContent
              description={description}
              setDescription={setDescription}
              title={title}
              setTitle={setTitle}
              functionName={functionName}
              setFunctionName={setFunctionName}
              lineNumber={lineNumber}
              setLineNumber={setLineNumber}
              tags={tags}
              setTags={setTags}
              filePath={filePath}
              setFilePath={setFilePath}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-[#3e3e42]">
          <button
            onClick={closeModal}
            className="px-4 py-1.5 text-xs bg-[#3c3c3c] hover:bg-[#4a4a4a] text-[#cccccc] rounded transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={
              noteType === "meeting"
                ? !title || !meetingDate || !audioFile
                : !description
            }
            className="px-4 py-1.5 text-xs bg-[#0e639c] hover:bg-[#1177bb] text-[#ffffff] rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {noteType === "meeting" ? "Save Meeting" : "Save Note"}
          </button>
        </div>
      </div>
    </div>
  );
}
