"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, Square } from "lucide-react";
import { formatDuration } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const MAX_SECONDS = 10 * 60;

function pickMimeType() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) ?? "";
}

function extensionFor(mimeType: string) {
  if (mimeType.includes("mp4")) return "m4a";
  if (mimeType.includes("ogg")) return "ogg";
  return "webm";
}

export function VoiceRecorder({
  disabled,
  onRecording,
}: {
  disabled?: boolean;
  onRecording: (file: File) => void;
}) {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef<number>(0);
  const aliveRef = useRef(true);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!recording) return;

    const timer = window.setInterval(() => {
      const next = Math.floor((Date.now() - startedAtRef.current) / 1000);
      setElapsed(next);
      if (next >= MAX_SECONDS) {
        stopRecording();
      }
    }, 250);

    return () => window.clearInterval(timer);
  }, [recording]);

  useEffect(() => {
    aliveRef.current = true;
    return () => {
      aliveRef.current = false;
      stopTracks();
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
    };
  }, []);

  function stopTracks() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  function stopRecording() {
    const recorder = recorderRef.current;
    if (recorder && recorder.state === "recording") {
      recorder.stop();
    }
  }

  async function startRecording() {
    setError(null);

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("This browser cannot record audio. Upload a wav/mp3/m4a file instead.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError("Recording failed. Try uploading an audio file instead.");
        setRecording(false);
        stopTracks();
      };

      recorder.onstop = () => {
        const type = recorder.mimeType || mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        stopTracks();
        setRecording(false);
        recorderRef.current = null;

        if (!aliveRef.current) return;

        if (blob.size < 1024) {
          setError("Recording was too short. Try again.");
          return;
        }

        const file = new File([blob], `recording.${extensionFor(type)}`, { type });
        onRecording(file);
      };

      startedAtRef.current = Date.now();
      setElapsed(0);
      setRecording(true);
      try {
        recorder.start(250);
      } catch {
        recorder.start();
      }
    } catch {
      setError("Microphone access was blocked. Allow it, or upload an audio file.");
      stopTracks();
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        {recording ? (
          <Button type="button" variant="danger" disabled={disabled} onClick={stopRecording}>
            <Square className="size-3.5 fill-current" />
            Stop
          </Button>
        ) : (
          <Button type="button" variant="secondary" disabled={disabled} onClick={() => void startRecording()}>
            <Mic className="size-4" />
            Record audio
          </Button>
        )}
      </div>

      {recording ? (
        <p className="mt-3 flex items-center justify-center gap-2 text-sm font-medium text-danger">
          <span className="size-2 animate-pulse rounded-full bg-danger" />
          Recording {formatDuration(elapsed)}
        </p>
      ) : (
        <p className="mt-3 text-xs text-gray-500">Up to 10 minutes. Stop when you are done, then analyse.</p>
      )}

      {error ? <p className="mt-2 text-sm text-danger">{error}</p> : null}
    </div>
  );
}
