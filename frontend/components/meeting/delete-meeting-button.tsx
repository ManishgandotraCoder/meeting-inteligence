"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { meetingApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/modal";

export function DeleteMeetingButton({
  meetingId,
  title,
  redirectTo,
  label = "Remove",
  compact = false,
}: {
  meetingId: string;
  title: string;
  redirectTo?: string;
  label?: string;
  compact?: boolean;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function onOpen(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    event.stopPropagation();
    setError(null);
    setOpen(true);
  }

  async function onConfirm() {
    try {
      setPending(true);
      setError(null);
      await meetingApi.remove(meetingId);
      setOpen(false);
      setPending(false);
      if (redirectTo) {
        router.push(redirectTo);
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove the transcript.");
      setPending(false);
    }
  }

  return (
    <>
      <Button
        type="button"
        variant={compact ? "ghost" : "danger"}
        className={
          compact ? "h-9 px-2.5 text-danger hover:bg-danger-soft hover:text-danger" : "h-9 px-3"
        }
        disabled={pending}
        onClick={onOpen}
        aria-label={`Remove ${title}`}
      >
        <Trash2 className="size-4" />
        {pending ? "Removing…" : compact ? null : label}
      </Button>

      <ConfirmDialog
        open={open}
        onClose={() => {
          if (!pending) setOpen(false);
        }}
        onConfirm={onConfirm}
        title="Remove this meeting?"
        description={`“${title}” will be deleted, including the transcript, insights, and any chat evidence. This cannot be undone.`}
        confirmLabel="Remove meeting"
        cancelLabel="Keep meeting"
        pending={pending}
        error={error}
        variant="danger"
      />
    </>
  );
}
