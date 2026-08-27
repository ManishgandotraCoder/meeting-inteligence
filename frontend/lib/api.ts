import { config } from "@/lib/config";
import type {
  MeetingDetail,
  MeetingListItem,
  MeetingUploadResponse,
} from "@/types/meeting";
import type { AskMeetingResponse } from "@/types/chat";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${config.apiUrl}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload = (await response.json()) as { detail?: string; message?: string };
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Keep fallback message when the response has no JSON body.
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const meetingApi = {
  list(): Promise<MeetingListItem[]> {
    return apiFetch<MeetingListItem[]>("/meetings");
  },

  get(meetingId: string): Promise<MeetingDetail> {
    return apiFetch<MeetingDetail>(`/meetings/${meetingId}`);
  },

  create(formData: FormData): Promise<MeetingUploadResponse> {
    return apiFetch<MeetingUploadResponse>("/meetings", {
      method: "POST",
      body: formData,
    });
  },

  remove(meetingId: string): Promise<void> {
    return apiFetch<void>(`/meetings/${meetingId}`, {
      method: "DELETE",
    });
  },

  ask(
    meetingId: string,
    question: string,
    history: { role: "user" | "assistant"; content: string }[] = [],
  ): Promise<AskMeetingResponse> {
    return apiFetch<AskMeetingResponse>(`/meetings/${meetingId}/chat`, {
      method: "POST",
      body: JSON.stringify({
        question,
        history: history.slice(-6).map((item) => ({
          role: item.role,
          content: item.content,
        })),
      }),
    });
  },
};
