const TabButton = ({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) => {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-1.5 px-3 py-1 text-xs rounded transition-colors
        ${
          active
            ? "bg-[#1e1e1e] text-[#ffffff]"
            : "text-[#cccccc] hover:bg-[#2a2d2e]"
        }
      `}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
};

export default TabButton;
