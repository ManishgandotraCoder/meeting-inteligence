import { Bot, UserRound } from "lucide-react";
import type { ChatMessage } from "@/types/chat";

export function ChatMessageBubble({
  message,
}: {
  message: ChatMessage;
}) {
  const assistant = message.role === "assistant";

  return (
    <div className={assistant ? "" : "flex justify-end"}>
      <div className={assistant ? "max-w-3xl" : "max-w-[min(100%,36rem)]"}>
        <div className="mb-1.5 flex items-center gap-2 text-xs font-medium text-gray-500">
          {assistant ? <Bot className="size-3.5" /> : <UserRound className="size-3.5" />}
          {assistant ? "Smart Meet" : "You"}
        </div>

        <div
          className={
            assistant
              ? "rounded-2xl bg-page px-4 py-3 text-sm leading-7 text-gray-700"
              : "rounded-2xl bg-brand px-4 py-2.5 text-sm leading-6 text-white"
          }
        >
          {message.content}
        </div>
      </div>
    </div>
  );
}
