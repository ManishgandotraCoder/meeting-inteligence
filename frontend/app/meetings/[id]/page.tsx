import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { meetingApi, ApiError } from "@/lib/api";
import { MeetingWorkspace } from "@/components/meeting/meeting-workspace";

type PageProps = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { id } = await params;

  try {
    const meeting = await meetingApi.get(id);
    return { title: meeting.title };
  } catch {
    return { title: "Meeting" };
  }
}

export default async function MeetingPage({ params }: PageProps) {
  const { id } = await params;

  try {
    const meeting = await meetingApi.get(id);
    return (
      <main className="mx-auto flex h-full min-h-0 w-full max-w-7xl flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6">
        <Suspense>
          <MeetingWorkspace meeting={meeting} />
        </Suspense>
      </main>
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
