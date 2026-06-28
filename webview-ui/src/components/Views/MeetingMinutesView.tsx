import { useState, useEffect } from "react";
import {
  Calendar,
  Clock,
  Users,
  Tag,
  GripHorizontal,
  CalendarX,
} from "lucide-react";
import { vscode } from "../../utilities/vscodeApi";

interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  attendees: string[];
  content: string;
  tags: string[];
  actionItems: string[];
}

// Shape returned by the backend GET /meetings (cached) endpoint.
interface BackendMeetingChunk {
  id: number;
  raw_text: string;
  summary_text: string;
  start_time_sec: number | null;
  end_time_sec: number | null;
  speaker_names: string[];
  meta: Record<string, any> | null;
}

interface BackendMeeting {
  id: number;
  title: string;
  date: string | null;
  duration_sec: number | null;
  language: string | null;
  project_name: string;
  meta: Record<string, any> | null;
  company_id: number;
  chunks: BackendMeetingChunk[];
}

// Map the backend meeting + chunks into the display shape this view renders.
function mapBackendMeeting(m: BackendMeeting): Meeting {
  const chunks = m.chunks ?? [];
  const attendees = Array.from(
    new Set(chunks.flatMap((c) => c.speaker_names ?? [])),
  );
  const content = chunks
    .map((c) => c.summary_text || c.raw_text)
    .filter(Boolean)
    .join("\n\n");
  return {
    id: String(m.id),
    title: m.title,
    date: m.date ?? "",
    duration: `${Math.round((m.duration_sec ?? 0) / 60)} min`,
    attendees,
    content,
    tags: m.meta?.tags ?? [m.project_name],
    actionItems: m.meta?.actionItems ?? [],
  };
}

export function MeetingMinutesView() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [topHeight, setTopHeight] = useState(50); // percentage
  const [isDragging, setIsDragging] = useState(false);

  // request the cached meetings from the vsc side on mount and listen
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const message = event.data;
      if (message.command === "meetings_data") {
        const mapped = ((message.data as BackendMeeting[]) ?? []).map(
          mapBackendMeeting,
        );
        setMeetings(mapped);
        setSelectedMeeting(mapped[0] ?? null);
        setLoading(false);
      } else if (message.command === "meetings_error") {
        setMeetings([]);
        setSelectedMeeting(null);
        setLoading(false);
      }
    };
    window.addEventListener("message", handleMessage);
    vscode.postMessage("getMeetings");
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return;

    const container = document.getElementById("meetings-container");
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const newHeight =
      ((e.clientY - containerRect.top) / containerRect.height) * 100;

    // Constrain between 20% and 80%
    if (newHeight >= 20 && newHeight <= 80) {
      setTopHeight(newHeight);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // add and remove mouse event listeners
  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      return () => {
        window.removeEventListener("mousemove", handleMouseMove);
        window.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [isDragging]);

  // empty/loading state
  if (meetings.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-[#1e1e1e] text-center p-6">
        {loading ? (
          <p className="text-xs text-[#6a6a6a] font-mono">Loading meetings…</p>
        ) : (
          <>
            <CalendarX className="w-10 h-10 text-[#3e3e42] mb-3" />
            <p className="text-sm text-[#cccccc] font-mono mb-1">
              No meetings found
            </p>
            <p className="text-xs text-[#6a6a6a] font-mono">
              Recorded meetings will appear here once processed.
            </p>
          </>
        )}
      </div>
    );
  }

  return (
    <div
      id="meetings-container"
      className="h-full flex flex-col bg-[#1e1e1e] relative"
    >
      {/* Meeting List */}
      <div
        className="overflow-auto p-2 space-y-2"
        style={{ height: selectedMeeting ? `${topHeight}%` : "100%" }}
      >
        {meetings.map((meeting) => (
          <MeetingCard
            key={meeting.id}
            meeting={meeting}
            selected={selectedMeeting?.id === meeting.id}
            onClick={() => setSelectedMeeting(meeting)}
          />
        ))}
      </div>

      {/* Resize Handle */}
      {selectedMeeting && (
        <div
          onMouseDown={handleMouseDown}
          className={`
            flex items-center justify-center
            border-t border-b border-[#3e3e42]
            bg-[#252526] cursor-ns-resize
            transition-colors
            ${isDragging ? "bg-[#007acc]" : "hover:bg-[#2a2d2e]"}
          `}
          style={{ height: "4px" }}
        >
          <GripHorizontal
            className={`w-4 h-4 transition-colors ${isDragging ? "text-[#ffffff]" : "text-[#6a6a6a]"}`}
            style={{
              position: "absolute",
              pointerEvents: "none",
            }}
          />
        </div>
      )}

      {/* Selected Meeting Details - Expandable Bottom Panel */}
      {selectedMeeting && (
        <div
          className="border-t border-[#3e3e42] bg-[#252526] overflow-auto"
          style={{ height: `${100 - topHeight}%` }}
        >
          <MeetingDetails meeting={selectedMeeting} />
        </div>
      )}
    </div>
  );
}

function MeetingCard({
  meeting,
  selected,
  onClick,
}: {
  meeting: Meeting;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full p-3 rounded border text-left transition-colors
        ${
          selected
            ? "bg-[#37373d] border-[#007acc]"
            : "bg-[#1e1e1e] border-[#3e3e42] hover:bg-[#2a2d2e]"
        }
      `}
    >
      <h3 className="text-xs text-[#ffffff] mb-2 line-clamp-2">
        {meeting.title}
      </h3>

      <div className="flex items-center gap-3 text-[10px] text-[#6a6a6a] mb-2">
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          {meeting.date ? new Date(meeting.date).toLocaleDateString() : "—"}
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {meeting.duration}
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {meeting.tags.slice(0, 2).map((tag) => (
          <span
            key={tag}
            className="px-1.5 py-0.5 bg-[#252526] border border-[#3e3e42] rounded text-[10px] text-[#4ec9b0] font-mono"
          >
            {tag}
          </span>
        ))}
        {meeting.tags.length > 2 && (
          <span className="px-1.5 py-0.5 text-[10px] text-[#6a6a6a]">
            +{meeting.tags.length - 2}
          </span>
        )}
      </div>
    </button>
  );
}

function MeetingDetails({ meeting }: { meeting: Meeting }) {
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-base text-[#ffffff] mb-3">{meeting.title}</h1>

        <div className="flex flex-wrap gap-4 text-xs text-[#cccccc] mb-3">
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4 text-[#6a6a6a]" />
            {meeting.date ? new Date(meeting.date).toLocaleString() : "—"}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4 text-[#6a6a6a]" />
            {meeting.duration}
          </div>
          {meeting.attendees.length > 0 && (
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4 text-[#6a6a6a]" />
              {meeting.attendees.join(", ")}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Tag className="w-3 h-3 text-[#6a6a6a]" />
          <div className="flex flex-wrap gap-1">
            {meeting.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-[#252526] border border-[#3e3e42] rounded text-xs text-[#4ec9b0] font-mono"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mb-6 p-4 bg-[#252526] border border-[#3e3e42] rounded">
        <div className="prose prose-invert prose-sm max-w-none">
          <div className="space-y-2 font-mono text-xs text-[#cccccc] whitespace-pre-wrap leading-relaxed">
            {meeting.content || "No transcript available for this meeting."}
          </div>
        </div>
      </div>

      {/* Action Items */}
      {meeting.actionItems.length > 0 && (
        <div className="p-4 bg-[#252526] border border-[#3e3e42] rounded">
          <h3 className="text-sm text-[#ffffff] mb-3 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-[#f48771] rounded-full" />
            Action Items
          </h3>
          <div className="space-y-2">
            {meeting.actionItems.map((item, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <div className="w-4 h-4 border border-[#3e3e42] rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                  <div className="w-2 h-2 bg-transparent" />
                </div>
                <span className="text-[#cccccc] font-mono">{item}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
