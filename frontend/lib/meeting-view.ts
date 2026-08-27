export const MEETING_VIEWS = ["chat", "overview", "transcript", "insights"] as const;

export type MeetingView = (typeof MEETING_VIEWS)[number];

export function isMeetingDetailPath(pathname: string) {
  return pathname.startsWith("/meetings/") && pathname !== "/meetings/new";
}

export function parseMeetingView(value: string | null): MeetingView {
  if (value === "overview" || value === "transcript" || value === "insights") {
    return value;
  }
  return "chat";
}

export function meetingViewHref(
  pathname: string,
  current: { toString(): string },
  view: MeetingView,
) {
  const next = new URLSearchParams(current.toString());
  if (view === "chat") next.delete("tab");
  else next.set("tab", view);
  const query = next.toString();
  return query ? `${pathname}?${query}` : pathname;
}
