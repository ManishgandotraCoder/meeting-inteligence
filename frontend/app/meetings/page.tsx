import type { Metadata } from "next";
import Link from "next/link";
import { Plus } from "lucide-react";
import { meetingApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { MeetingCard } from "@/components/meeting/meeting-card";

export const metadata: Metadata = {
  title: "Meetings",
};

export default async function MeetingsPage() {
  const meetings = await meetingApi.list();

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 sm:py-6">
      <div className="mb-5 flex flex-col justify-between gap-3 sm:mb-6 sm:flex-row sm:items-end">
        <div className="min-w-0">
          <p className="text-sm font-medium text-brand">Workspace</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">Your meetings</h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-gray-500">
            Upload transcripts, review decisions and action items, and ask grounded
            questions about what happened.
          </p>
        </div>
      </div>

      {meetings.length === 0 ? (
        <EmptyState
          title="No meetings yet"
          description="Upload your first transcript to create a searchable meeting workspace."
          action={
            <Button asChild>
              <Link href="/meetings/new">
                <Plus className="size-4" />
                Upload transcript
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {meetings.map((meeting) => (
            <MeetingCard key={meeting.id} meeting={meeting} />
          ))}
        </div>
      )}
    </main>
  );
}
