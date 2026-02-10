import React from "react";

export function TypeButton({
  icon,
  label,
  selected,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        flex flex-col items-center gap-1 p-3 rounded border transition-colors
        ${
          selected
            ? "bg-[#0e639c] border-[#007acc] text-[#ffffff]"
            : "bg-[#3c3c3c] border-[#3e3e42] text-[#cccccc] hover:bg-[#4a4a4a]"
        }
      `}
    >
      {icon}
      <span className="text-xs">{label}</span>
    </button>
  );
}
