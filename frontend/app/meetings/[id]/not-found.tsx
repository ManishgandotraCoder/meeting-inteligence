import Link from "next/link";
import { SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function MeetingNotFound() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-lg items-center px-5 text-center">
      <div className="w-full rounded-2xl border bg-white p-6 shadow-sm sm:p-8">
        <SearchX className="mx-auto mb-4 size-8 text-brand" />
        <h1 className="text-xl font-semibold">Meeting not found</h1>
        <p className="mt-2 text-sm text-gray-500">
          This meeting may have been removed or the link may be incorrect.
        </p>
        <Button className="mt-5" asChild>
          <Link href="/meetings">Back to meetings</Link>
        </Button>
      </div>
    </div>
  );
}
