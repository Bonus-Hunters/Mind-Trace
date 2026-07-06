import { useState } from "react";
import { vscode } from "../../../utilities/vscodeApi";
import type { ResolvedFile } from "./fileLinkUtils";

interface Props {
  name: string;
  matches: ResolvedFile[];
}

function openFile(path: string) {
  vscode.postMessage("openFile", { path });
}

/**
 * Renders a single filename mentioned in an assistant reply.
 *  - 0 matches  → plain, non-clickable text
 *  - 1 match    → clickable link that opens the file
 *  - 2+ matches → non-clickable; hover reveals a popover listing every match
 */
export function FileNameToken({ name, matches }: Props) {
  const [showPopover, setShowPopover] = useState(false);

  // Not found in the workspace — render as ordinary text.
  if (matches.length === 0) {
    return <span>{name}</span>;
  }

  // Unique match — a direct clickable link.
  if (matches.length === 1) {
    return (
      <button
        type="button"
        title={matches[0].relativePath}
        onClick={() => openFile(matches[0].path)}
        className="text-[#4daafc] underline underline-offset-2 hover:text-[#6cb6ff] cursor-pointer bg-transparent p-0 font-mono"
      >
        {name}
      </button>
    );
  }

  // Ambiguous — show a hover popover with every matching file.
  return (
    <span
      className="relative inline-block"
      onMouseEnter={() => setShowPopover(true)}
      onMouseLeave={() => setShowPopover(false)}
    >
      <span className="text-[#4daafc] underline decoration-dotted underline-offset-2 cursor-default">
        {name}
      </span>

      {showPopover && (
        <div className="absolute left-0 top-full z-50 mt-1 min-w-[180px] max-w-[320px] rounded border border-[#3e3e42] bg-[#252526] p-1 shadow-lg">
          <div className="px-2 py-1 text-[10px] uppercase tracking-wide text-[#6a6a6a]">
            {matches.length} files named {name}
          </div>
          {matches.map((file) => (
            <button
              key={file.path}
              type="button"
              title={file.path}
              onClick={() => openFile(file.path)}
              className="block w-full truncate rounded px-2 py-1 text-left text-[11px] text-[#cccccc] hover:bg-[#2a2d2e] hover:text-[#4daafc] cursor-pointer bg-transparent font-mono"
            >
              {file.relativePath}
            </button>
          ))}
        </div>
      )}
    </span>
  );
}
