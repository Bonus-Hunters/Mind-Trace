import { Calendar } from "lucide-react";

const ProjectContent = ({
  projectName,
  setProjectName,
  creationDate,
  setCreationDate,
}: any) => {
  return (
    <>
      {/* Project Name */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Project Name *
        </label>
        <input
          type="text"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="Enter project name..."
          className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
        />
      </div>

      {/* Creation Date */}
      <div>
        <label className="block text-xs text-[#cccccc] mb-2 font-mono">
          Creation Date *
        </label>
        <div className="relative">
          <input
            type="date"
            value={creationDate}
            onChange={(e) => setCreationDate(e.target.value)}
            className="w-full px-3 py-2 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
          />
          <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6a6a6a] pointer-events-none" />
        </div>
      </div>
    </>
  );
};

export default ProjectContent;
