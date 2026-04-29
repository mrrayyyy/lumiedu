"use client";

import { useCallback, useRef, useState } from "react";

type RecorderState = "idle" | "recording" | "processing";

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      const base64 = dataUrl.split(",", 2)[1] ?? "";
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export function useVoiceRecorder() {
  const [state, setState] = useState<RecorderState>("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start(100);
      setState("recording");
    } catch {
      setState("idle");
    }
  }, []);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      setState("idle");
      return null;
    }

    setState("processing");

    return new Promise<string | null>((resolve) => {
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        recorder.stream.getTracks().forEach((t) => t.stop());
        mediaRecorderRef.current = null;
        chunksRef.current = [];

        try {
          const base64 = await blobToBase64(blob);
          setState("idle");
          resolve(base64);
        } catch {
          setState("idle");
          resolve(null);
        }
      };

      recorder.stop();
    });
  }, []);

  const cancelRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stream.getTracks().forEach((t) => t.stop());
      recorder.stop();
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
    setState("idle");
  }, []);

  return {
    state,
    isRecording: state === "recording",
    isProcessing: state === "processing",
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
