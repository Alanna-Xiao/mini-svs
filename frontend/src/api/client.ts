import type {
  InstrumentSummary,
  Project,
  RenderResponse,
  VoicebankSummary,
} from "../types/project";

type ApiErrorPayload = {
  error?: { code?: string; message?: string };
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

export async function listInstruments(): Promise<InstrumentSummary[]> {
  const response = await fetch("/api/instruments");
  if (!response.ok) {
    throw new ApiError("Could not load instruments.", "instrument_list_failed", response.status);
  }
  return (await response.json()) as InstrumentSummary[];
}

export async function listVoicebanks(): Promise<VoicebankSummary[]> {
  const response = await fetch("/api/voicebanks");
  if (!response.ok) {
    throw new ApiError("Could not load voicebanks.", "voicebank_list_failed", response.status);
  }
  return (await response.json()) as VoicebankSummary[];
}

export async function renderProject(project: Project, trackIds?: string[]): Promise<RenderResponse> {
  const response = await fetch("/api/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...project, trackIds }),
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new ApiError(
      payload.error?.message ?? "Render failed.",
      payload.error?.code ?? "render_failed",
      response.status,
    );
  }
  return (await response.json()) as RenderResponse;
}
