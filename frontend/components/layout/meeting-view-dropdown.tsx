"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  Check,
  CheckSquare2,
  ChevronDown,
  FileText,
  MessageSquareText,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  MEETING_VIEWS,
  meetingViewHref,
  parseMeetingView,
  type MeetingView,
} from "@/lib/meeting-view";

const views: {
  id: MeetingView;
  label: string;
  icon: React.ElementType;
}[] = [
  { id: "chat", label: "Chat", icon: MessageSquareText },
  { id: "overview", label: "Overview", icon: Sparkles },
  { id: "transcript", label: "Transcript", icon: FileText },
  { id: "insights", label: "Insights", icon: CheckSquare2 },
];

export function MeetingViewDropdown() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const active = parseMeetingView(searchParams.get("tab"));
  const current = views.find((view) => view.id === active) ?? views[0];
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [active]);

  return (
    <div ref={rootRef} className="relative min-w-0">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((value) => !value)}
        className="inline-flex h-9 max-w-full min-w-0 items-center gap-1.5 rounded-lg px-2 text-sm font-medium text-ink transition hover:bg-page focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 sm:px-2.5"
      >
        <current.icon className="size-4 shrink-0 text-brand" />
        <span className="truncate">{current.label}</span>
        <ChevronDown
          className={cn("size-4 shrink-0 text-gray-400 transition", open && "rotate-180")}
        />
      </button>

      {open ? (
        <div
          id={menuId}
          role="menu"
          className="absolute left-0 top-full z-50 mt-1 w-48 overflow-hidden rounded-lg border border-slate-200/80 bg-white py-1 shadow-lg"
        >
          {MEETING_VIEWS.map((id) => {
            const view = views.find((item) => item.id === id)!;
            const selected = view.id === active;

            return (
              <Link
                key={view.id}
                href={meetingViewHref(pathname, searchParams, view.id)}
                scroll={false}
                role="menuitem"
                aria-current={selected ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2 px-2.5 py-1.5 text-sm transition hover:bg-page",
                  selected ? "font-medium text-brand" : "text-gray-600",
                )}
              >
                <view.icon className="size-4 shrink-0" />
                <span className="flex-1">{view.label}</span>
                {selected ? <Check className="size-3.5" /> : null}
              </Link>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
