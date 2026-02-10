import React from "react";

const TagsInput = ({ tags, setTags }: any) => {
  return (
    <div>
      <label className="block text-xs text-[#cccccc] mb-2 font-mono">
        Tags (comma-separated)
      </label>
      <input
        type="text"
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        placeholder="planning, sprint, review"
        className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
      />
    </div>
  );
};

export default TagsInput;
