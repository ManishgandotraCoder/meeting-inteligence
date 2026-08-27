export type SourceCitation = {
  segmentId: string;
  speaker: string;
  timestamp: string;
  text: string;
  score?: number;
};

export type ChatHistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceCitation[];
};

export type AskMeetingResponse = {
  answer: string;
  sources: SourceCitation[];
};
