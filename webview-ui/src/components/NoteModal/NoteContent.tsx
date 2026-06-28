import { useEffect, useState } from "react";
import TagsInput from "./TagsInput";
import { vscode } from "../../utilities/vscodeApi.ts";

interface ProjectOption {
  value: string;
  label: string;
}

const noteTypesOptions = [
  { value: "general", label: "General" },
  { value: "optimization", label: "Optimization" },
  { value: "todo", label: "TODO" },
  { value: "bug", label: "Bug" },
  { value: "omit", label: "Ommit Task" },
  { value: "suggestion", label: "Suggestion" },
];

const NoteContent = ({
  description,
  setDescription,
  title,
  setTitle,
  functionName,
  setFunctionName,
  lineNumber,
  setLineNumber,
  tags,
  setTags,
  filePath,
  setFilePath,
  noteCategory,
  setNoteCategory,
  projectName,
  setProjectName,
  moduleName,
  setModuleName,
}: any) => {
  const [projectOptions, setProjectOptions] = useState<ProjectOption[]>([]);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const message = event.data;
      if (message.command === "projects_data") {
        const options = ((message.data as string[]) ?? []).map((name) => ({
          value: name,
          label: name,
        }));
        setProjectOptions(options);
        // default the dropdown to the first project once loaded
        if (options.length > 0) setProjectName(options[0].value);
      }
    };
    window.addEventListener("message", handleMessage);
    // request the company's projects from the extension host
    vscode.postMessage("getProjects");
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  setNoteCategory(noteTypesOptions[0].value);
  return (
    <>
      {/* Mandatory Fields */}
      {/* Description */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Description *
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter note description "
          rows={6}
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors resize-none font-mono"
        />
      </div>
      {/* Note Type Selection */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Note Type *
        </label>
        <select
          value={noteCategory}
          onChange={(e) => setNoteCategory(e.target.value)}
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] focus:outline-none focus:border-[#007acc] transition-colors font-mono appearance-none cursor-pointer"
        >
          {/*TODO: change styling for the title*/}
          {noteTypesOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {/* Project Name Selection */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Project Name *
        </label>
        <select
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] focus:outline-none focus:border-[#007acc] transition-colors font-mono appearance-none cursor-pointer"
        >
          {/*TODO: change styling for the title*/}
          {projectOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {/* --- Optional Fields --- */}
      {/* Title */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter note title..."
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
        />
      </div>

      {/* Function Name  */}
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

      {/* Module Name  */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Module Name
        </label>
        <input
          type="text"
          value={moduleName}
          onChange={(e) => setModuleName(e.target.value)}
          placeholder="AI"
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
        />
      </div>

      {/* Line Number  */}
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
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          File Path
        </label>
        <input
          type="text"
          value={filePath}
          onChange={(e) => setFilePath(e.target.value)}
          placeholder="src/components/Example.tsx"
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
        />
      </div>
      {/* Tags */}
      <TagsInput tags={tags} setTags={setTags} />
    </>
  );
};

export default NoteContent;
