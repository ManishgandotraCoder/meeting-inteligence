"use client";

import { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  CalendarDays,
  CheckSquare2,
  ListTodo,
  Users,
} from "lucide-react";
import type { MeetingDetail } from "@/types/meeting";
import { cn, formatDate } from "@/lib/utils";
import { meetingViewHref, parseMeetingView } from "@/lib/meeting-view";
import { speakerInitials, speakerTheme } from "@/lib/speakers";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/meeting/status-badge";
import { OverviewPanel } from "@/components/meeting/overview-panel";
import { TranscriptPanel } from "@/components/meeting/transcript-panel";
import { InsightsPanel } from "@/components/meeting/insights-panel";
import { ChatPanel } from "@/components/chat/chat-panel";
import { DeleteMeetingButton } from "@/components/meeting/delete-meeting-button";

export function MeetingWorkspace({ meeting }: { meeting: MeetingDetail }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeTab = parseMeetingView(searchParams.get("tab"));
  const [focusedSegmentId, setFocusedSegmentId] = useState<string | null>(null);
  const fillHeight = activeTab === "transcript" || activeTab === "chat";

  function jumpToSegment(segmentId: string) {
    setFocusedSegmentId(segmentId);
    router.replace(meetingViewHref(pathname, searchParams, "transcript"), {
      scroll: false,
    });
  }

  return (
    <div
      className={cn(
        "grid min-h-0 flex-1 gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]",
        fillHeight ? "h-full min-h-0 overflow-hidden xl:items-stretch" : "xl:items-start",
      )}
    >
      <div
        className={cn(
          "min-w-0 xl:col-start-1 xl:row-start-1",
          fillHeight ? "flex h-full min-h-0 min-w-0 flex-col gap-4" : "space-y-4",
        )}
      >
        <MobileMeetingBar meeting={meeting} />

        <div className={cn("min-w-0", activeTab !== "overview" && "hidden")}>
          <OverviewPanel meeting={meeting} />
        </div>
        <div
          className={cn(
            "min-h-0 min-w-0",
            activeTab === "transcript" ? "flex h-full min-h-0 min-w-0 flex-1 flex-col" : "hidden",
          )}
        >
          <TranscriptPanel
            segments={meeting.transcript}
            participants={meeting.participants}
            focusedSegmentId={focusedSegmentId}
            onFocusedHandled={() => setFocusedSegmentId(null)}
          />
        </div>
        <div className={cn("min-w-0", activeTab !== "insights" && "hidden")}>
          <InsightsPanel meeting={meeting} onJumpToSegment={jumpToSegment} />
        </div>
        <div
          className={cn(
            "min-h-0",
            activeTab === "chat" ? "flex h-full min-h-0 flex-1 flex-col" : "hidden",
          )}
        >
          <ChatPanel meetingId={meeting.id} />
        </div>
      </div>

      <aside className="hidden xl:sticky xl:top-[calc(var(--header-h)+1rem)] xl:col-start-2 xl:row-start-1 xl:block">
        <MeetingDetails meeting={meeting} />
      </aside>
    </div>
  );
}

function MobileMeetingBar({ meeting }: { meeting: MeetingDetail }) {
  return (
    <Card className="shrink-0 p-3.5 xl:hidden">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-2">
            <StatusBadge status={meeting.status} />
            <h1 className="min-w-0 truncate text-base font-semibold tracking-tight">
              {meeting.title}
            </h1>
          </div>
          <p className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
            <span className="inline-flex items-center gap-1.5">
              <CalendarDays className="size-3.5" />
              {formatDate(meeting.createdAt)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Users className="size-3.5" />
              {meeting.participants.length} speakers
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CheckSquare2 className="size-3.5" />
              {meeting.decisions.length} decisions
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ListTodo className="size-3.5" />
              {meeting.actionItems.length} actions
            </span>
          </p>
        </div>
        <DeleteMeetingButton
          meetingId={meeting.id}
          title={meeting.title}
          redirectTo="/meetings"
          compact
        />
      </div>

      {meeting.participants.length > 0 ? (
        <ul className="no-scrollbar mt-3 flex gap-2 overflow-x-auto">
          {meeting.participants.map((speaker) => {
            const theme = speakerTheme(speaker, meeting.participants);
            return (
              <li
                key={speaker}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-page py-1 pl-1 pr-2.5"
              >
                <span
                  className={cn(
                    "flex size-5 items-center justify-center rounded-full text-[10px] font-semibold",
                    theme.avatar,
                  )}
                >
                  {speakerInitials(speaker)}
                </span>
                <span className="text-xs font-medium">{speaker}</span>
              </li>
            );
          })}
        </ul>
      ) : null}
    </Card>
  );
}

function MeetingDetails({ meeting }: { meeting: MeetingDetail }) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-3">
        <StatusBadge status={meeting.status} />
        <DeleteMeetingButton
          meetingId={meeting.id}
          title={meeting.title}
          redirectTo="/meetings"
          compact
        />
      </div>

      <h1 className="mt-3 text-base font-semibold tracking-tight">{meeting.title}</h1>

      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-500">
        <p className="flex items-center gap-1.5">
          <CalendarDays className="size-3.5 shrink-0" />
          {formatDate(meeting.createdAt)}
        </p>
        <p className="flex items-center gap-1.5">
          <Users className="size-3.5 shrink-0" />
          {meeting.participants.length} speakers
        </p>
      </div>

      {meeting.participants.length > 0 ? (
        <ul className="mt-3.5 flex flex-wrap gap-2">
          {meeting.participants.map((speaker) => {
            const theme = speakerTheme(speaker, meeting.participants);
            return (
              <li
                key={speaker}
                className="inline-flex max-w-full items-center gap-1.5 rounded-full bg-page py-1 pl-1 pr-2.5"
              >
                <span
                  className={cn(
                    "flex size-6 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold",
                    theme.avatar,
                  )}
                >
                  {speakerInitials(speaker)}
                </span>
                <span className="truncate text-xs font-medium">{speaker}</span>
              </li>
            );
          })}
        </ul>
      ) : null}

      <div className="mt-4 grid grid-cols-2 gap-2">
        <Metric
          icon={<CheckSquare2 className="size-3.5 text-emerald-600" />}
          label="Decisions"
          value={meeting.decisions.length}
        />
        <Metric
          icon={<ListTodo className="size-3.5 text-blue-600" />}
          label="Actions"
          value={meeting.actionItems.length}
        />
      </div>
    </Card>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl bg-page px-3 py-2.5 ring-1 ring-slate-200">
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        {icon}
        {label}
      </div>
      <p className="mt-0.5 text-xl font-semibold tabular-nums tracking-tight">{value}</p>
    </div>
  );
}
