import React from "react";
import TagsInput from "./TagsInput";

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
}: any) => {
  return (
    <>
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
