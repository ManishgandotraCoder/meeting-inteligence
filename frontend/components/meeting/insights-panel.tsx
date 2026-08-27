import { AlertTriangle, ArrowUpRight, CheckCircle2, Clock3, ListTodo, UserRound } from "lucide-react";
import type { MeetingDetail } from "@/types/meeting";
import { Card } from "@/components/ui/card";

export function InsightsPanel({
  meeting,
  onJumpToSegment,
}: {
  meeting: MeetingDetail;
  onJumpToSegment?: (segmentId: string) => void;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card className="p-4 sm:p-5">
        <SectionTitle
          icon={<CheckCircle2 className="size-4 text-emerald-600" />}
          title="Decisions"
          count={meeting.decisions.length}
        />

        <div className="mt-4 space-y-2.5">
          {meeting.decisions.map((decision) => (
            <div key={decision.id} className="rounded-xl border border-slate-200/80 bg-page p-3.5">
              <p className="text-sm leading-6">{decision.text}</p>
              {decision.source ? (
                <SourceLink
                  speaker={decision.source.speaker}
                  timestamp={decision.source.timestamp}
                  onClick={
                    onJumpToSegment
                      ? () => onJumpToSegment(decision.source!.segmentId)
                      : undefined
                  }
                />
              ) : null}
            </div>
          ))}
          {meeting.decisions.length === 0 && <Empty label="No decisions extracted." />}
        </div>
      </Card>

      <Card className="p-4 sm:p-5">
        <SectionTitle
          icon={<ListTodo className="size-4 text-blue-600" />}
          title="Action items"
          count={meeting.actionItems.length}
        />

        <div className="mt-4 space-y-2.5">
          {meeting.actionItems.map((item) => (
            <div key={item.id} className="rounded-xl border border-slate-200/80 bg-page p-3.5">
              <p className="text-sm font-medium leading-6">{item.task}</p>
              <div className="mt-2.5 flex flex-wrap gap-3 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <UserRound className="size-3.5" />
                  {item.owner || "Unassigned"}
                </span>
                {item.dueDate ? (
                  <span className="flex items-center gap-1">
                    <Clock3 className="size-3.5" />
                    {item.dueDate}
                  </span>
                ) : null}
              </div>
              {item.source ? (
                <SourceLink
                  speaker={item.source.speaker}
                  timestamp={item.source.timestamp}
                  onClick={
                    onJumpToSegment
                      ? () => onJumpToSegment(item.source!.segmentId)
                      : undefined
                  }
                />
              ) : null}
            </div>
          ))}
          {meeting.actionItems.length === 0 && <Empty label="No action items extracted." />}
        </div>
      </Card>

      <Card className="p-4 sm:col-span-2 sm:p-5 md:col-span-2">
        <SectionTitle
          icon={<AlertTriangle className="size-4 text-amber-700" />}
          title="Risks & blockers"
          count={meeting.risks.length}
        />

        <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
          {meeting.risks.map((risk) => (
            <div key={risk.id} className="rounded-xl border border-amber-200/80 bg-amber-50/70 p-3.5">
              <p className="text-sm leading-6 text-gray-700">{risk.text}</p>
              {risk.source ? (
                <SourceLink
                  speaker={risk.source.speaker}
                  timestamp={risk.source.timestamp}
                  onClick={
                    onJumpToSegment
                      ? () => onJumpToSegment(risk.source!.segmentId)
                      : undefined
                  }
                />
              ) : null}
            </div>
          ))}
          {meeting.risks.length === 0 && <Empty label="No risks extracted." />}
        </div>
      </Card>
    </div>
  );
}

function SectionTitle({
  icon,
  title,
  count,
}: {
  icon: React.ReactNode;
  title: string;
  count: number;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <h2 className="font-semibold">{title}</h2>
      </div>
      <span className="rounded-full bg-page px-2 py-0.5 text-[11px] text-gray-500">
        {count}
      </span>
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return <p className="text-sm text-gray-500">{label}</p>;
}

function SourceLink({
  speaker,
  timestamp,
  onClick,
}: {
  speaker: string;
  timestamp: string;
  onClick?: () => void;
}) {
  const label = `${speaker} · ${timestamp}`;

  if (!onClick) {
    return <p className="mt-2 text-xs text-gray-400">{label}</p>;
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-brand hover:text-brand-hover"
    >
      {label}
      <ArrowUpRight className="size-3" />
    </button>
  );
}
