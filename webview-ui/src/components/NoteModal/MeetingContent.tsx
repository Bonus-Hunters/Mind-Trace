import { useEffect } from "react";
import { X, Calendar, Upload } from "lucide-react";
import TagsInput from "./TagsInput";
import { vscode } from "../../utilities/vscodeApi.ts";

const languageOptions = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "it", label: "Italian" },
  { value: "pt", label: "Portuguese" },
  { value: "ru", label: "Russian" },
  { value: "zh", label: "Chinese" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
  { value: "ar", label: "Arabic" },
  { value: "hi", label: "Hindi" },
];

const projectOptions = [{ value: "Mozilla Issues", label: "Mozilla Issues" }];

const handleUpload = () => {
  vscode.postMessage("selectAudioFile");
};

const MeetingContent = ({
  title,
  meetingDate,
  language,
  tags,
  audioFile,
  setTitle,
  setMeetingDate,
  setLanguage,
  setTags,
  setAudioFile,
  setProjectName,
  projectName,
}: any) => {
  useEffect(() => {
    // TODO: should execute each time user upload a video
    // define the listener function
    const handleMessage = (event: MessageEvent) => {
      const message = event.data;

      switch (message.command) {
        case "audioProcessingFinished":
          console.log(
            "Received audio processing result in react:",
            message.data.filename,
          );
          setAudioFile({
            filename: message.data.filename,
            size: message.data.size,
          });
          break;
      }
    };

    // Add the listener to the window
    window.addEventListener("message", handleMessage);

    // Clean up the listener when the component unmounts
    return () => window.removeEventListener("message", handleMessage);
  }, []);
  setProjectName(projectOptions[0].value); // Set default project name on component mount
  return (
    <>
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Meeting Title *
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter meeting title..."
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
        />
      </div>

      {/* Meeting Date */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Meeting Date *
        </label>
        <div className="relative">
          <input
            type="date"
            value={meetingDate}
            onChange={(e) => setMeetingDate(e.target.value)}
            className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
          />
          <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6a6a6a] pointer-events-none" />
        </div>
      </div>

      {/* Language Selection */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Language *
        </label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] focus:outline-none focus:border-[#007acc] transition-colors font-mono appearance-none cursor-pointer"
        >
          {languageOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {/* Project Name */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Project Name *
        </label>
        <select
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] focus:outline-none focus:border-[#007acc] transition-colors font-mono appearance-none cursor-pointer"
        >
          {projectOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {/* Tags */}
      <TagsInput tags={tags} setTags={setTags} />

      {/* Audio File Upload */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Audio File *
        </label>
        <div className="space-y-2" onClick={handleUpload}>
          <label
            htmlFor="audio-upload"
            className="flex items-center justify-center gap-2 w-full px-3 py-3 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] hover:bg-[#4a4a4a] transition-colors cursor-pointer"
          >
            <Upload className="w-4 h-4" />
            <span className="font-mono">Browse Audio File</span>
          </label>

          {!audioFile && (
            <p className="text-xs text-[#6a6a6a] font-mono">
              Supported formats: WAV, MP3, MP4, M4A
            </p>
          )}
        </div>
        {audioFile && (
          <div className="flex items-center justify-between px-3 py-2 bg-[#252526] border border-[#3e3e42] rounded">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-xs text-[#4ec9b0] font-mono">📁</span>
              <span className="text-xs text-[#cccccc] font-mono truncate">
                {audioFile.filename}
              </span>
              <span className="text-xs text-[#6a6a6a] font-mono flex-shrink-0">
                ({(audioFile.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </div>
            <button
              onClick={() => setAudioFile(null)}
              className="ml-2 p-1 hover:bg-[#3c3c3c] rounded transition-colors flex-shrink-0"
            >
              <X className="w-3 h-3 text-[#cccccc]" />
            </button>
          </div>
        )}
      </div>
    </>
  );
};

export default MeetingContent;
