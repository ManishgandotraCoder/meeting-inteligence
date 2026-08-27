import Link from "next/link";
import { ArrowUpRight, CheckSquare2, MessageSquareText, Users } from "lucide-react";
import type { MeetingListItem } from "@/types/meeting";
import { formatDate } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/meeting/status-badge";
import { DeleteMeetingButton } from "@/components/meeting/delete-meeting-button";

export function MeetingCard({ meeting }: { meeting: MeetingListItem }) {
  return (
    <Card className="h-full p-4 transition duration-200 hover:border-brand/20 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <StatusBadge status={meeting.status} />
        <DeleteMeetingButton meetingId={meeting.id} title={meeting.title} compact />
      </div>

      <Link href={`/meetings/${meeting.id}`} className="group mt-3 block">
        <h2 className="line-clamp-2 text-base font-semibold tracking-tight group-hover:text-brand">
          {meeting.title}
        </h2>
        <p className="mt-1 text-xs text-gray-500">{formatDate(meeting.createdAt)}</p>
      </Link>

      <div className="mt-3.5 grid grid-cols-3 gap-2 border-t pt-3 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <Users className="size-3.5" />
          {meeting.participantCount}
        </div>
        <div className="flex items-center gap-1.5">
          <MessageSquareText className="size-3.5" />
          {meeting.decisionCount}
        </div>
        <div className="flex items-center gap-1.5">
          <CheckSquare2 className="size-3.5" />
          {meeting.actionItemCount}
        </div>
      </div>

      <Link
        href={`/meetings/${meeting.id}`}
        className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-brand hover:text-brand-hover"
      >
        Open
        <ArrowUpRight className="size-3.5" />
      </Link>
    </Card>
  );
}
