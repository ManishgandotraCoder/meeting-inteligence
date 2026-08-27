"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown,
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  MessagesSquare,
  Search,
  X,
} from "lucide-react";
import type { TranscriptSegment } from "@/types/meeting";
import { cn } from "@/lib/utils";
import { speakerInitials, speakerList, speakerTheme } from "@/lib/speakers";
import { Card } from "@/components/ui/card";

export function TranscriptPanel({
  segments,
  participants = [],
  focusedSegmentId = null,
  onFocusedHandled,
}: {
  segments: TranscriptSegment[];
  participants?: string[];
  focusedSegmentId?: string | null;
  onFocusedHandled?: () => void;
}) {
  const threadRef = useRef<HTMLDivElement>(null);
  const onFocusedHandledRef = useRef(onFocusedHandled);
  onFocusedHandledRef.current = onFocusedHandled;
  const [query, setQuery] = useState("");
  const [speakerFilter, setSpeakerFilter] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [matchIndex, setMatchIndex] = useState(0);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showJumpLatest, setShowJumpLatest] = useState(false);

  const speakers = useMemo(
    () => speakerList(participants, segments.map((segment) => segment.speaker)),
    [participants, segments],
  );

  const speakerCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const segment of segments) {
      counts.set(segment.speaker, (counts.get(segment.speaker) ?? 0) + 1);
    }
    return counts;
  }, [segments]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    return segments.filter((segment) => {
      if (speakerFilter && segment.speaker !== speakerFilter) return false;
      if (!normalized) return true;
      return (
        segment.text.toLowerCase().includes(normalized) ||
        segment.speaker.toLowerCase().includes(normalized)
      );
    });
  }, [query, segments, speakerFilter]);

  const safeMatchIndex =
    filtered.length === 0 ? 0 : Math.min(matchIndex, filtered.length - 1);
  const activeMatchId = query.trim() ? filtered[safeMatchIndex]?.id : null;

  useEffect(() => {
    setMatchIndex(0);
  }, [query, speakerFilter]);

  useEffect(() => {
    if (!focusedSegmentId) return;
    setSelectedId(focusedSegmentId);
    setSpeakerFilter(null);
    setQuery("");
  }, [focusedSegmentId]);

  useEffect(() => {
    const id = focusedSegmentId ?? activeMatchId;
    if (!id) return;

    const frame = window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => scrollToSegment(threadRef.current, id));
    });

    if (!focusedSegmentId) {
      return () => window.cancelAnimationFrame(frame);
    }

    const timer = window.setTimeout(() => onFocusedHandledRef.current?.(), 900);
    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(timer);
    };
  }, [activeMatchId, focusedSegmentId]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setQuery("");
        setSpeakerFilter(null);
        setSelectedId(null);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  async function copySegment(segment: TranscriptSegment) {
    try {
      await navigator.clipboard.writeText(
        `${segment.speaker} (${segment.startTime}): ${segment.text}`,
      );
      setCopiedId(segment.id);
      window.setTimeout(() => {
        setCopiedId((current) => (current === segment.id ? null : current));
      }, 1600);
    } catch {
      // Clipboard can be blocked in some browsers; selection still works.
    }
  }

  function cycleMatch(direction: 1 | -1) {
    if (filtered.length === 0) return;
    setMatchIndex((current) => (current + direction + filtered.length) % filtered.length);
  }

  function onThreadScroll() {
    const el = threadRef.current;
    if (!el) return;
    setShowJumpLatest(el.scrollHeight - el.scrollTop - el.clientHeight > 140);
  }

  function jumpToLatest() {
    const el = threadRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }

  return (
    <Card className="flex h-full min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <header className="min-w-0 shrink-0 border-b border-slate-200/80 bg-white p-3.5 sm:p-4">
        <div className="relative w-full">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search the conversation…"
            aria-label="Search transcript"
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                cycleMatch(event.shiftKey ? -1 : 1);
              }
            }}
            className={cn(
              "h-10 w-full rounded-xl border border-gray-200 bg-page pl-9 text-sm outline-none transition focus:border-brand focus:bg-white",
              query.trim() ? "pr-28" : "pr-3",
            )}
          />
          <div className="absolute right-1.5 top-1/2 flex -translate-y-1/2 items-center gap-0.5">
            {query.trim() ? (
              <>
                <span className="px-1 font-mono text-[11px] tabular-nums text-gray-400">
                  {filtered.length === 0 ? "0" : `${safeMatchIndex + 1}/${filtered.length}`}
                </span>
                <IconButton
                  label="Previous match"
                  onClick={() => cycleMatch(-1)}
                  disabled={filtered.length === 0}
                >
                  <ChevronUp className="size-3.5" />
                </IconButton>
                <IconButton
                  label="Next match"
                  onClick={() => cycleMatch(1)}
                  disabled={filtered.length === 0}
                >
                  <ChevronDown className="size-3.5" />
                </IconButton>
                <IconButton label="Clear search" onClick={() => setQuery("")}>
                  <X className="size-3.5" />
                </IconButton>
              </>
            ) : null}
          </div>
        </div>

        {speakers.length > 0 ? (
          <div className="no-scrollbar mt-3 flex min-w-0 w-full flex-nowrap items-center gap-2 overflow-x-auto overscroll-x-contain pb-0.5">
            <button
              type="button"
              onClick={() => setSpeakerFilter(null)}
              aria-pressed={speakerFilter === null}
              className={cn(
                "inline-flex shrink-0 items-center whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium ring-1 transition",
                speakerFilter === null
                  ? "bg-ink text-white ring-ink"
                  : "bg-page text-gray-600 ring-slate-200 hover:bg-white",
              )}
            >
              All · {segments.length}
            </button>
            {speakers.map((speaker) => {
              const theme = speakerTheme(speaker, speakers);
              const active = speakerFilter === speaker;

              return (
                <button
                  key={speaker}
                  type="button"
                  onClick={() =>
                    setSpeakerFilter((current) => (current === speaker ? null : speaker))
                  }
                  aria-pressed={active}
                  className={cn(
                    "inline-flex shrink-0 flex-row flex-nowrap items-center gap-2 whitespace-nowrap rounded-full px-2.5 py-1.5 text-xs font-medium ring-1 transition",
                    active ? theme.chipActive : theme.chip,
                  )}
                >
                  <span
                    className={cn(
                      "flex size-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold",
                      theme.avatar,
                    )}
                  >
                    {speakerInitials(speaker)}
                  </span>
                  <span className="whitespace-nowrap">{speaker}</span>
                  <span
                    className={cn(
                      "shrink-0 tabular-nums",
                      active ? "text-white/80" : "opacity-70",
                    )}
                  >
                    {speakerCounts.get(speaker) ?? 0}
                  </span>
                </button>
              );
            })}
          </div>
        ) : null}
      </header>

      <div className="relative min-h-0 flex-1">
        <div
          ref={threadRef}
          onScroll={onThreadScroll}
          className="h-full overflow-y-auto [background-image:radial-gradient(rgba(15,23,42,0.045)_1px,transparent_1px)] [background-size:18px_18px] bg-[var(--surface-muted)]"
        >
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-1 px-3 py-4 sm:px-5 sm:py-5">
          {segments.length === 0 ? (
            <div className="px-4 py-16 text-center">
              <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
                <MessagesSquare className="size-5 text-gray-400" />
              </div>
              <p className="mt-4 font-medium">No conversation yet</p>
              <p className="mt-1 text-sm text-gray-500">
                The transcript will appear here once processing is complete.
              </p>
            </div>
          ) : null}

          {segments.length > 0 ? filtered.map((segment, index) => {
            const previous = filtered[index - 1];
            const next = filtered[index + 1];
            const theme = speakerTheme(segment.speaker, speakers);
            const firstInGroup = previous?.speaker !== segment.speaker;
            const lastInGroup = next?.speaker !== segment.speaker;
            const showDivider = shouldShowTimeDivider(previous, segment);
            const selected = selectedId === segment.id;
            const focused = focusedSegmentId === segment.id;
            const isMatch = activeMatchId === segment.id;

            return (
              <div key={segment.id}>
                {showDivider ? (
                  <div className="my-3.5 flex items-center gap-3">
                    <div className="h-px flex-1 bg-slate-200/80" />
                    <span className="rounded-full bg-white/90 px-2.5 py-1 font-mono text-[11px] text-gray-500 shadow-sm ring-1 ring-slate-200/80">
                      {segment.startTime}
                    </span>
                    <div className="h-px flex-1 bg-slate-200/80" />
                  </div>
                ) : null}

                <article
                  id={`segment-${segment.id}`}
                  className={cn(
                    "flex gap-2.5",
                    firstInGroup ? "mt-3" : "mt-1",
                  )}
                >
                  <div className="flex w-8 shrink-0 justify-center sm:w-9">
                    {firstInGroup ? (
                      <button
                        type="button"
                        aria-label={`Show only ${segment.speaker}`}
                        onClick={() =>
                          setSpeakerFilter((current) =>
                            current === segment.speaker ? null : segment.speaker,
                          )
                        }
                        className={cn(
                          "flex size-8 items-center justify-center rounded-full text-xs font-semibold transition hover:scale-105 sm:size-9",
                          theme.avatar,
                        )}
                      >
                        {speakerInitials(segment.speaker)}
                      </button>
                    ) : null}
                  </div>

                  <div className="flex min-w-0 max-w-[min(88%,42rem)] flex-col items-start sm:max-w-[min(78%,42rem)]">
                    {firstInGroup ? (
                      <button
                        type="button"
                        onClick={() =>
                          setSpeakerFilter((current) =>
                            current === segment.speaker ? null : segment.speaker,
                          )
                        }
                        className={cn(
                          "mb-1 px-1 text-left text-xs font-semibold hover:underline",
                          theme.name,
                        )}
                      >
                        {segment.speaker}
                      </button>
                    ) : null}

                    <div
                      className={cn(
                        "group relative max-w-full",
                        (selected || copiedId === segment.id) && "mb-8",
                      )}
                    >
                      <button
                        type="button"
                        onClick={() =>
                          setSelectedId((current) =>
                            current === segment.id ? null : segment.id,
                          )
                        }
                        className={cn(
                          "w-fit max-w-full break-words px-3.5 py-2.5 text-left text-sm leading-6 transition sm:text-[15px]",
                          theme.incoming,
                          lastInGroup
                            ? "rounded-[20px] rounded-bl-md"
                            : "rounded-[20px]",
                          (selected || isMatch) && "ring-2 ring-brand/60",
                          focused && "transcript-focus",
                        )}
                      >
                        <HighlightedText
                          text={segment.text}
                          query={query}
                          markClassName={theme.incomingMark}
                        />
                        <span
                          className={cn(
                            "mt-1.5 block text-right font-mono text-[10px] tabular-nums",
                            theme.incomingMeta,
                          )}
                        >
                          {segment.startTime}
                        </span>
                      </button>

                      <div
                        className={cn(
                          "absolute top-full left-0 z-10 mt-1 flex items-center gap-1",
                          selected || copiedId === segment.id
                            ? "opacity-100"
                            : "pointer-events-none opacity-0 group-hover:pointer-events-auto group-hover:opacity-100",
                        )}
                      >
                        <button
                          type="button"
                          onClick={() => void copySegment(segment)}
                          className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1 text-[11px] font-medium text-gray-600 shadow-sm ring-1 ring-slate-200/80 hover:text-ink"
                        >
                          {copiedId === segment.id ? (
                            <>
                              <Check className="size-3 text-emerald-600" />
                              Copied
                            </>
                          ) : (
                            <>
                              <Copy className="size-3" />
                              Copy
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </article>
              </div>
            );
          }) : null}

          {segments.length > 0 && filtered.length === 0 ? (
            <div className="px-4 py-16 text-center">
              <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
                <Search className="size-5 text-gray-400" />
              </div>
              <p className="mt-4 font-medium">No messages match</p>
              <p className="mt-1 text-sm text-gray-500">
                Try another speaker or a different search phrase.
              </p>
              {query || speakerFilter ? (
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    setSpeakerFilter(null);
                  }}
                  className="mt-4 text-sm font-medium text-brand hover:text-brand-hover"
                >
                  Clear filters
                </button>
              ) : null}
            </div>
          ) : null}
          </div>
        </div>

        {showJumpLatest ? (
          <button
            type="button"
            onClick={jumpToLatest}
            aria-label="Jump to latest message"
            className="absolute bottom-4 right-4 z-10 inline-flex size-10 items-center justify-center rounded-full bg-white text-ink shadow-md ring-1 ring-slate-200 transition hover:bg-page"
          >
            <ArrowDown className="size-4" />
          </button>
        ) : null}
      </div>
    </Card>
  );
}

function HighlightedText({
  text,
  query,
  markClassName,
}: {
  text: string;
  query: string;
  markClassName: string;
}) {
  const needle = query.trim();
  if (!needle) return <>{text}</>;

  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const parts = text.split(new RegExp(`(${escaped})`, "gi"));

  return (
    <>
      {parts.map((part, index) =>
        part.toLowerCase() === needle.toLowerCase() ? (
          <mark key={`${part}-${index}`} className={cn("rounded px-0.5", markClassName)}>
            {part}
          </mark>
        ) : (
          <span key={`${part}-${index}`}>{part}</span>
        ),
      )}
    </>
  );
}

function IconButton({
  label,
  onClick,
  disabled,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className="inline-flex size-7 items-center justify-center rounded-lg text-gray-500 transition hover:bg-white hover:text-ink disabled:opacity-30"
    >
      {children}
    </button>
  );
}

function shouldShowTimeDivider(
  previous: TranscriptSegment | undefined,
  current: TranscriptSegment,
) {
  if (!previous) return true;
  const previousSeconds = parseTimestamp(previous.startTime);
  const currentSeconds = parseTimestamp(current.startTime);
  if (previousSeconds == null || currentSeconds == null) {
    return previous.startTime !== current.startTime && currentSeconds == null;
  }
  return currentSeconds - previousSeconds >= 90;
}

function scrollToSegment(thread: HTMLDivElement | null, id: string) {
  if (!thread) return;
  const node = document.getElementById(`segment-${id}`);
  if (!node) return;

  const threadRect = thread.getBoundingClientRect();
  const nodeRect = node.getBoundingClientRect();
  const offset =
    thread.scrollTop +
    (nodeRect.top - threadRect.top) -
    thread.clientHeight / 2 +
    nodeRect.height / 2;

  thread.scrollTo({ top: Math.max(0, offset), behavior: "smooth" });
}

function parseTimestamp(value: string) {
  const match = value.trim().match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
  if (!match) return null;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  const seconds = Number(match[3] ?? 0);
  if (match[3] == null && hours > 23) {
    return hours * 60 + minutes;
  }
  return hours * 3600 + minutes * 60 + seconds;
}
