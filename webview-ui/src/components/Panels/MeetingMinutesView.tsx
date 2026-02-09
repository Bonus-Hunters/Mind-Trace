import { useState } from "react";
import { Calendar, Clock, Users, Tag, Filter } from "lucide-react";

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

const mockMeetings: Meeting[] = [
  {
    id: "1",
    title: "Sprint Planning - Q1 2026",
    date: "2025-12-04T15:00:00",
    duration: "90 min",
    attendees: ["Dev Team", "PM", "Design"],
    tags: ["planning", "sprint", "q1-2026"],
    content: `## Agenda
1. Review Q4 2025 performance
2. Q1 2026 roadmap discussion
3. Resource allocation
4. Timeline and milestones

## Key Decisions
- Focus on performance improvements in January
- API v2 migration scheduled for February
- New dashboard design approved for March release
- Weekly sync meetings on Mondays at 10 AM

## Discussion Points
**Performance Optimization:**
- Current page load time averaging 3.2s
- Target: reduce to under 1.5s
- Will require database query optimization and caching layer

**API v2 Migration:**
- Breaking changes documented
- Migration guide to be published by end of December
- Deprecation timeline: 6 months from launch

## Risks & Concerns
- Resource constraints due to holiday season
- Potential delays in third-party integrations
- Need backup plan for cloud provider migration`,
    actionItems: [
      "@john: Create performance benchmarks by Dec 10",
      "@sarah: Draft API migration guide",
      "@mike: Review infrastructure requirements",
      "@team: Submit Q1 goals by Friday",
    ],
  },
  {
    id: "2",
    title: "Security Review Meeting",
    date: "2025-12-05T14:00:00",
    duration: "60 min",
    attendees: ["Security Team", "Backend Team"],
    tags: ["security", "review", "critical"],
    content: `## Security Audit Results
- Overall score: B+
- Critical issues: 2 (both related to auth)
- Medium issues: 5
- Low issues: 12

## Authentication Vulnerabilities Discussed
1. **Token Expiration Policy**
   - Current: 24 hours (too long)
   - Recommended: 1 hour with refresh tokens
   
2. **Rate Limiting**
   - Currently not implemented on all endpoints
   - Need to add to: /api/auth/*, /api/user/*

## Mitigation Strategies
- Implement sliding session windows
- Add Redis-based rate limiting
- Enable 2FA for admin accounts
- Regular security audits (quarterly)

## Compliance Considerations
- GDPR: Data retention policies need update
- SOC2: Audit trail implementation required
- CCPA: User data export functionality needed`,
    actionItems: [
      "@security: Implement rate limiting by Dec 15",
      "@backend: Update token expiration logic",
      "@compliance: Draft data retention policy",
      "@all: Complete security training by month end",
    ],
  },
  {
    id: "3",
    title: "Feature Kickoff: Dark Mode",
    date: "2025-12-06T10:30:00",
    duration: "45 min",
    attendees: ["Frontend Team", "Design", "PM"],
    tags: ["feature", "ui", "dark-mode"],
    content: `## Feature Overview
Implement system-wide dark mode with smooth transitions and theme persistence.

## Design Specifications
- Use CSS variables for all color values
- Support system preference detection
- Manual toggle in user settings
- Smooth transition animations (200ms)

## Technical Approach
1. Define color tokens in CSS variables
2. Create theme toggle context
3. Persist preference in localStorage
4. Respect prefers-color-scheme media query

## Scope
**In Scope:**
- All main application pages
- Dashboard components
- Settings panel
- Theme toggle UI

**Out of Scope:**
- Email templates (separate ticket)
- Marketing pages (handled by marketing team)
- Third-party embedded widgets

## Timeline
- Week 1: Setup infrastructure
- Week 2: Implement toggle and persistence
- Week 3: QA and polish
- Week 4: Release to beta users`,
    actionItems: [
      "@design: Finalize dark mode color palette",
      "@frontend: Create theme provider component",
      "@qa: Prepare test cases for accessibility",
      "@pm: Draft beta user communication",
    ],
  },
];

const allTags = [
  "planning",
  "sprint",
  "security",
  "review",
  "feature",
  "ui",
  "critical",
  "q1-2026",
  "dark-mode",
];

export function MeetingMinutesView() {
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(
    mockMeetings[0],
  );

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* Meeting List */}
      <div className="flex-1 overflow-auto p-2 space-y-2">
        {mockMeetings.map((meeting) => (
          <MeetingCard
            key={meeting.id}
            meeting={meeting}
            selected={selectedMeeting?.id === meeting.id}
            onClick={() => setSelectedMeeting(meeting)}
          />
        ))}
      </div>

      {/* Selected Meeting Details - Expandable Bottom Panel */}
      {selectedMeeting && (
        <div className="border-t border-[#3e3e42] bg-[#252526] max-h-96 overflow-auto">
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
          {new Date(meeting.date).toLocaleDateString()}
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
            {new Date(meeting.date).toLocaleString()}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4 text-[#6a6a6a]" />
            {meeting.duration}
          </div>
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4 text-[#6a6a6a]" />
            {meeting.attendees.join(", ")}
          </div>
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
            {meeting.content}
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
