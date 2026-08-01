import type { Project, RenderResponse } from "../types/project";

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
