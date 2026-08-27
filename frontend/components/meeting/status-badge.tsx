import { AlertCircle, Check, LoaderCircle, Upload } from "lucide-react";
import type { ElementType } from "react";
import { cn } from "@/lib/utils";
import type { MeetingStatus } from "@/types/meeting";

const styles: Record<MeetingStatus, string> = {
  uploaded: "bg-brand-soft text-brand ring-brand/15",
  processing: "bg-amber-50 text-amber-800 ring-amber-700/15",
  ready: "bg-emerald-50 text-emerald-800 ring-emerald-700/15",
  failed: "bg-danger-soft text-danger ring-danger/15",
};

const icons: Record<MeetingStatus, ElementType> = {
  uploaded: Upload,
  processing: LoaderCircle,
  ready: Check,
  failed: AlertCircle,
};

export function StatusBadge({ status }: { status: MeetingStatus }) {
  const Icon = icons[status];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium capitalize ring-1 ring-inset",
        styles[status],
      )}
    >
      <Icon className={cn("size-3", status === "processing" && "animate-spin")} />
      {status}
    </span>
  );
}
