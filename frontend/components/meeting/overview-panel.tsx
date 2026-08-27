import { AlertTriangle, CheckCircle2, ListTodo } from "lucide-react";
import type { MeetingDetail } from "@/types/meeting";
import { Card } from "@/components/ui/card";

export function OverviewPanel({ meeting }: { meeting: MeetingDetail }) {
  return (
    <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
      <Card className="p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-brand">
          AI summary
        </p>
        <h2 className="mt-1.5 text-lg font-semibold sm:text-xl">What happened</h2>
        <p className="mt-3 whitespace-pre-line text-sm leading-7 text-gray-600">
          {meeting.summary || "Summary will appear when processing is complete."}
        </p>
      </Card>

      <div className="space-y-4">
        <Card className="p-5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="size-4 text-emerald-600" />
            <h3 className="font-semibold">Top decisions</h3>
          </div>
          <div className="mt-3.5 space-y-2.5">
            {meeting.decisions.slice(0, 3).map((decision) => (
              <div key={decision.id} className="rounded-xl bg-page p-3">
                <p className="text-sm leading-6">{decision.text}</p>
              </div>
            ))}
            {meeting.decisions.length === 0 && (
              <p className="text-sm text-gray-500">No decisions extracted.</p>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2">
            <ListTodo className="size-4 text-blue-600" />
            <h3 className="font-semibold">Open actions</h3>
          </div>
          <div className="mt-3.5 space-y-2.5">
            {meeting.actionItems.slice(0, 3).map((item) => (
              <div key={item.id} className="rounded-xl bg-page p-3">
                <p className="text-sm font-medium leading-6">{item.task}</p>
                <p className="mt-1 text-xs text-gray-500">
                  {item.owner || "Unassigned"}
                  {item.dueDate ? ` · Due ${item.dueDate}` : ""}
                </p>
              </div>
            ))}
            {meeting.actionItems.length === 0 && (
              <p className="text-sm text-gray-500">No action items extracted.</p>
            )}
          </div>
        </Card>

        {meeting.risks.length > 0 && (
          <Card className="p-5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-amber-700" />
              <h3 className="font-semibold">Risks</h3>
            </div>
            <p className="mt-3 text-sm leading-6 text-gray-600">
              {meeting.risks[0].text}
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
