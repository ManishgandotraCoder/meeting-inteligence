export type SpeakerTheme = {
  avatar: string;
  incoming: string;
  outgoing: string;
  chip: string;
  chipActive: string;
  name: string;
  incomingMeta: string;
  outgoingMeta: string;
  incomingMark: string;
  outgoingMark: string;
};

export const SPEAKER_THEMES: SpeakerTheme[] = [
  {
    avatar: "bg-sky-600 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-sky-100",
    outgoing: "bg-sky-600 text-white shadow-sm",
    chip: "bg-sky-50 text-sky-800 ring-sky-200/80",
    chipActive: "bg-sky-600 text-white ring-sky-600",
    name: "text-sky-800",
    incomingMeta: "text-sky-700/70",
    outgoingMeta: "text-white/70",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
  {
    avatar: "bg-violet-600 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-violet-100",
    outgoing: "bg-violet-600 text-white shadow-sm",
    chip: "bg-violet-50 text-violet-800 ring-violet-200/80",
    chipActive: "bg-violet-600 text-white ring-violet-600",
    name: "text-violet-800",
    incomingMeta: "text-violet-700/70",
    outgoingMeta: "text-white/70",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
  {
    avatar: "bg-emerald-600 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-emerald-100",
    outgoing: "bg-emerald-600 text-white shadow-sm",
    chip: "bg-emerald-50 text-emerald-800 ring-emerald-200/80",
    chipActive: "bg-emerald-600 text-white ring-emerald-600",
    name: "text-emerald-800",
    incomingMeta: "text-emerald-700/70",
    outgoingMeta: "text-white/70",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
  {
    avatar: "bg-amber-500 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-amber-100",
    outgoing: "bg-amber-500 text-white shadow-sm",
    chip: "bg-amber-50 text-amber-900 ring-amber-200/80",
    chipActive: "bg-amber-500 text-white ring-amber-500",
    name: "text-amber-800",
    incomingMeta: "text-amber-800/70",
    outgoingMeta: "text-white/80",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
  {
    avatar: "bg-rose-600 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-rose-100",
    outgoing: "bg-rose-600 text-white shadow-sm",
    chip: "bg-rose-50 text-rose-800 ring-rose-200/80",
    chipActive: "bg-rose-600 text-white ring-rose-600",
    name: "text-rose-800",
    incomingMeta: "text-rose-700/70",
    outgoingMeta: "text-white/70",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
  {
    avatar: "bg-cyan-600 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-cyan-100",
    outgoing: "bg-cyan-600 text-white shadow-sm",
    chip: "bg-cyan-50 text-cyan-800 ring-cyan-200/80",
    chipActive: "bg-cyan-600 text-white ring-cyan-600",
    name: "text-cyan-800",
    incomingMeta: "text-cyan-700/70",
    outgoingMeta: "text-white/70",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
  {
    avatar: "bg-indigo-600 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-indigo-100",
    outgoing: "bg-indigo-600 text-white shadow-sm",
    chip: "bg-indigo-50 text-indigo-800 ring-indigo-200/80",
    chipActive: "bg-indigo-600 text-white ring-indigo-600",
    name: "text-indigo-800",
    incomingMeta: "text-indigo-700/70",
    outgoingMeta: "text-white/70",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
  {
    avatar: "bg-orange-600 text-white",
    incoming: "bg-white text-ink shadow-sm ring-1 ring-orange-100",
    outgoing: "bg-orange-600 text-white shadow-sm",
    chip: "bg-orange-50 text-orange-900 ring-orange-200/80",
    chipActive: "bg-orange-600 text-white ring-orange-600",
    name: "text-orange-800",
    incomingMeta: "text-orange-800/70",
    outgoingMeta: "text-white/70",
    incomingMark: "bg-amber-200 text-ink",
    outgoingMark: "bg-white/25 text-white",
  },
];

export function speakerList(participants: string[], fallback: string[]) {
  if (participants.length > 0) return participants;
  return [...new Set(fallback)];
}

export function speakerTheme(name: string, speakers: string[]): SpeakerTheme {
  const index = speakers.indexOf(name);
  const resolved = index >= 0 ? index : Math.abs(hashString(name));
  return SPEAKER_THEMES[resolved % SPEAKER_THEMES.length];
}

export function speakerInitials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

function hashString(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) | 0;
  }
  return hash;
}
