"use client";

import { useState } from "react";
import { Bot, Send } from "lucide-react";
import { meetingApi } from "@/lib/api";
import type { ChatMessage } from "@/types/chat";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { ChatMessageBubble } from "@/components/chat/chat-message";
import { SuggestedQuestions } from "@/components/chat/suggested-questions";

const suggestions = [
  "What decisions were made?",
  "What action items were assigned?",
  "What risks or blockers were discussed?",
  "Where did the team disagree?",
];

export function ChatPanel({
  meetingId,
}: {
  meetingId: string;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      sources: [],
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setLoading(true);
    setError(null);

    try {
      const response = await meetingApi.ask(
        meetingId,
        trimmed,
        messages.map((item) => ({ role: item.role, content: item.content })),
      );

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not answer the question.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
      <div className="shrink-0 border-b px-4 py-3.5 sm:px-5">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-brand-soft/50">
            <Bot className="size-4 text-brand" />
          </div>
          <div className="min-w-0">
            <h2 className="font-semibold">Ask Smart Meet</h2>
            <p className="text-xs text-gray-500">
              Grounded answers from this transcript only
            </p>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4 sm:p-5">
        {messages.length === 0 ? (
          <div className="mx-auto flex min-h-full max-w-2xl flex-col items-center justify-center px-2 py-6 text-center">
            <div className="mx-auto flex size-11 items-center justify-center rounded-2xl bg-brand-soft/50">
              <Bot className="size-5 text-brand" />
            </div>
            <h3 className="mt-4 font-semibold">Explore the meeting</h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-gray-500">
              Ask about decisions, ownership, disagreements, deadlines, risks, or
              anything else contained in the transcript.
            </p>
            <SuggestedQuestions suggestions={suggestions} onSelect={ask} />
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessageBubble key={message.id} message={message} />
          ))
        )}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Spinner />
            Thinking..
          </div>
        ) : null}

        {error ? (
          <p className="rounded-xl bg-danger-soft px-4 py-2.5 text-sm text-danger">{error}</p>
        ) : null}
      </div>

      <form
        className="shrink-0 border-t bg-white p-3 sm:p-4"
        onSubmit={(event) => {
          event.preventDefault();
          void ask(question);
        }}
      >
        <div className="flex gap-2 rounded-2xl border border-gray-200 bg-page p-2 focus-within:border-brand focus-within:bg-white">
          <textarea
            rows={1}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void ask(question);
              }
            }}
            placeholder="Ask a question about this meeting…"
            className="max-h-32 min-h-10 min-w-0 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-gray-400"
          />
          <button
            type="submit"
            disabled={!question.trim() || loading}
            aria-label="Send question"
            className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand text-white transition hover:bg-brand-hover disabled:opacity-40"
          >
            <Send className="size-4" />
          </button>
        </div>
        <p className="mt-2 px-1 text-xs text-gray-400">
          Smart Meet can make mistakes. Check the transcript for important details.
        </p>
      </form>
    </Card>
  );
}
