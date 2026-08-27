import type { Metadata } from "next";
import { UploadForm } from "@/components/meeting/upload-form";

export const metadata: Metadata = {
  title: "New meeting",
};

export default function NewMeetingPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-5 sm:px-6 sm:py-8">
      <div className="mb-5 sm:mb-6">
        <p className="text-sm font-medium text-brand">New meeting</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
          Add a meeting
        </h1>
        <p className="mt-1.5 text-sm leading-6 text-gray-500">
          Upload a labelled .txt transcript, or record / attach audio. Smart Meet
          parses it, indexes it for retrieval, and extracts key insights.
        </p>
      </div>

      <UploadForm />
    </main>
  );
}
