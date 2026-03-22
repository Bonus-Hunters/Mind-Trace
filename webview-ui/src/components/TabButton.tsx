const TabButton = ({
  icon,
  label,
  active = true,
  onClick,
  type,
  className = "",
  ...props
}: {
  icon?: React.ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
  className?: string;
  type: string;
}) => {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-1.5 px-3 py-1 text-xs rounded transition-colors ${className}
        ${
          type === "black"
            ? active
              ? "bg-[#1e1e1e] text-[#ffffff]"
              : "text-[#cccccc] hover:bg-[#2a2d2e]"
            : "bg-[#0e639c] hover:bg-[#1177bb] "
        }
      `}
    >
      {icon}
      {label}
    </button>
  );
};

export default TabButton;
