import type { SourceCitation } from "@/types/chat";

export type MeetingStatus = "uploaded" | "processing" | "ready" | "failed";

export type MeetingListItem = {
  id: string;
  title: string;
  status: MeetingStatus;
  createdAt: string;
  participantCount: number;
  decisionCount: number;
  actionItemCount: number;
};

export type TranscriptSegment = {
  id: string;
  speaker: string;
  startTime: string;
  endTime?: string | null;
  text: string;
};

export type Decision = {
  id: string;
  text: string;
  source?: SourceCitation | null;
};

export type ActionItem = {
  id: string;
  task: string;
  owner?: string | null;
  dueDate?: string | null;
  source?: SourceCitation | null;
};

export type Risk = {
  id: string;
  text: string;
  source?: SourceCitation | null;
};

export type MeetingDetail = {
  id: string;
  title: string;
  status: MeetingStatus;
  createdAt: string;
  participants: string[];
  summary: string;
  transcript: TranscriptSegment[];
  decisions: Decision[];
  actionItems: ActionItem[];
  risks: Risk[];
};

export type MeetingUploadResponse = {
  id: string;
  title: string;
  status: MeetingStatus;
};
