"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileAudio, FileText, Mic, UploadCloud, X } from "lucide-react";
import { meetingApi } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { VoiceRecorder } from "@/components/meeting/voice-recorder";

type Source = "transcript" | "voice";

const AUDIO_NAME = /\.(wav|mp3|m4a|webm|ogg|mp4|mpeg|mpga)$/i;

function isTranscriptFile(file: File) {
  return file.name.toLowerCase().endsWith(".txt") || file.type === "text/plain";
}

function isAudioFile(file: File) {
  return file.type.startsWith("audio/") || AUDIO_NAME.test(file.name);
}

export function UploadForm() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [source, setSource] = useState<Source>("transcript");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioMode = source === "voice";

  function selectFile(nextFile?: File, nextSource?: Source) {
    if (!nextFile) return;

    const transcript = isTranscriptFile(nextFile);
    const audio = isAudioFile(nextFile);

    if (!transcript && !audio) {
      setError("Upload a .txt transcript or an audio file (wav, mp3, m4a, webm).");
      return;
    }

    const resolved: Source = nextSource ?? (audio && !transcript ? "voice" : "transcript");

    if (resolved === "transcript" && !transcript) {
      setError("Please upload a .txt transcript.");
      return;
    }

    if (resolved === "voice" && !audio) {
      setError("Please upload an audio file (wav, mp3, m4a, webm).");
      return;
    }

    const maxBytes =
      resolved === "voice" ? 25 * 1024 * 1024 : 5 * 1024 * 1024;
    if (nextFile.size > maxBytes) {
      setError(
        resolved === "voice"
          ? "Audio must be smaller than 25 MB."
          : "Transcript must be smaller than 5 MB.",
      );
      return;
    }

    setSource(resolved);
    setFile(nextFile);
    setError(null);

    if (!title.trim()) {
      setTitle(
        nextFile.name
          .replace(/\.(txt|wav|mp3|m4a|webm|ogg|mp4|mpeg|mpga)$/i, "")
          .replace(/[-_]/g, " "),
      );
    }
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!file || !title.trim()) {
      setError(
        audioMode
          ? "Add a meeting title and a recording."
          : "Add a meeting title and transcript.",
      );
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const formData = new FormData();
      formData.append("title", title.trim());
      formData.append("file", file);

      const meeting = await meetingApi.create(formData);
      router.push(`/meetings/${meeting.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <Card className="p-5 sm:p-6">
        <div className="flex rounded-xl bg-page p-1">
          {(
            [
              { id: "transcript", label: "Transcript file", icon: FileText },
              { id: "voice", label: "Voice", icon: Mic },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setSource(item.id);
                setFile(null);
                setError(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              className={cn(
                "inline-flex h-9 flex-1 items-center justify-center gap-1.5 rounded-lg text-sm font-medium transition",
                source === item.id
                  ? "bg-white text-brand shadow-sm"
                  : "text-gray-600 hover:text-ink",
              )}
            >
              <item.icon className="size-4" />
              {item.label}
            </button>
          ))}
        </div>

        <label className="mt-5 block text-sm font-medium text-gray-800" htmlFor="title">
          Meeting title
        </label>
        <input
          id="title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="e.g. Product launch planning"
          className="mt-2 h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm outline-none transition placeholder:text-gray-400 focus:border-brand focus:ring-4 focus:ring-brand-soft/50"
        />

        <div
          className={[
            "mt-5 rounded-2xl border-2 border-dashed p-6 text-center transition sm:p-8",
            dragging ? "border-brand bg-brand-soft/40" : "border-gray-200 bg-page",
          ].join(" ")}
          onDragEnter={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={(event) => {
            event.preventDefault();
            setDragging(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            selectFile(event.dataTransfer.files[0], source);
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={
              audioMode
                ? "audio/*,.wav,.mp3,.m4a,.webm,.ogg"
                : ".txt,text/plain"
            }
            className="hidden"
            onChange={(event) => selectFile(event.target.files?.[0], source)}
          />

          {!file ? (
            <>
              <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-brand-soft">
                {audioMode ? (
                  <Mic className="size-5 text-brand" />
                ) : (
                  <UploadCloud className="size-5 text-brand" />
                )}
              </div>
              <p className="mt-4 text-sm font-medium">
                {audioMode ? "Record the meeting or drop audio" : "Drop your transcript here"}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {audioMode
                  ? "wav, mp3, m4a, or webm up to 25 MB"
                  : "Plain-text files up to 5 MB"}
              </p>
              {audioMode ? (
                <div className="mt-5">
                  <VoiceRecorder
                    disabled={submitting}
                    onRecording={(nextFile) => selectFile(nextFile, "voice")}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    className="mt-2"
                    onClick={() => inputRef.current?.click()}
                  >
                    Choose audio file
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  variant="secondary"
                  className="mt-5"
                  onClick={() => inputRef.current?.click()}
                >
                  Choose file
                </Button>
              )}
            </>
          ) : (
            <div className="mx-auto flex max-w-md items-center gap-3 rounded-lg border bg-white p-3 text-left">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-soft/50">
                {audioMode ? (
                  <FileAudio className="size-4 text-brand" />
                ) : (
                  <FileText className="size-4 text-brand" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="mt-0.5 text-xs text-gray-500">{formatBytes(file.size)}</p>
              </div>
              <button
                type="button"
                aria-label={audioMode ? "Remove recording" : "Remove transcript"}
                className="rounded-lg p-2 text-gray-400 hover:bg-brand-soft/50 hover:text-brand"
                onClick={() => {
                  setFile(null);
                  if (inputRef.current) inputRef.current.value = "";
                }}
              >
                <X className="size-4" />
              </button>
            </div>
          )}
        </div>

        {audioMode ? (
          <div className="mt-5 rounded-xl bg-page p-4">
            <p className="text-xs font-medium text-gray-700">Voice notes</p>
            <p className="mt-2 text-xs leading-5 text-gray-500">
              Audio is transcribed locally with Whisper, then indexed the same way as a
              .txt upload. Turns are timestamped; speakers are labelled{" "}
              <span className="font-medium text-gray-700">Speaker</span> unless you
              upload a named transcript. The first run downloads a local model and can
              take a minute.
            </p>
          </div>
        ) : (
          <div className="mt-5 rounded-xl bg-page p-4">
            <p className="text-xs font-medium text-gray-700">Any text format</p>
            <p className="mt-1 text-xs leading-5 text-gray-500">
              Labelled transcripts, chat exports, Zoom-style dumps, or loose
              meeting notes. If the layout is unfamiliar, the model reads it.
              Titles and participant lists are skipped.
            </p>
            <pre className="mt-2 overflow-x-auto text-xs leading-5 text-gray-500">
{`[00:00:12] Sarah:
We need to release next Friday.

Sarah: John will own the API.
John: Agreed.`}
            </pre>
          </div>
        )}

        {error ? (
          <p className="mt-3 rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">
            {error}
          </p>
        ) : null}

        <div className="mt-5 flex justify-end">
          <Button disabled={submitting || !file || !title.trim()} type="submit">
            {submitting ? <Spinner /> : <UploadCloud className="size-4" />}
            {submitting
              ? audioMode
                ? "Transcribing…"
                : "Processing…"
              : audioMode
                ? "Transcribe & analyse"
                : "Upload & analyse"}
          </Button>
        </div>
      </Card>
    </form>
  );
}
