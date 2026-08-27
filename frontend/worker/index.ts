interface Env {
  ASSETS: { fetch(request: Request): Promise<Response> };
  BACKEND_ORIGIN: string;
  BACKEND_GATEWAY_TOKEN: string;
}

const MAX_API_BODY_BYTES = 1_000_000;
const GATEWAY_HEADER = "x-mini-svs-gateway-token";

function apiError(status: number, code: string, message: string): Response {
  return Response.json(
    { error: { code, message } },
    { status, headers: { "cache-control": "no-store" } },
  );
}

export function createWorkerHandler(fetchOrigin: typeof fetch = fetch) {
  return async (request: Request, env: Env): Promise<Response> => {
    const requestUrl = new URL(request.url);
    if (!requestUrl.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);
    }

    const contentLength = Number(request.headers.get("content-length") ?? 0);
    if (contentLength > MAX_API_BODY_BYTES) {
      return apiError(413, "request_too_large", "API requests are limited to 1 MB.");
    }

    let target: URL;
    try {
      const origin = new URL(env.BACKEND_ORIGIN);
      if (origin.protocol !== "https:") {
        throw new Error("Backend origin must use HTTPS.");
      }
      target = new URL(origin);
    } catch {
      return apiError(500, "gateway_misconfigured", "The synthesis gateway is not configured.");
    }

    target.pathname = requestUrl.pathname.slice(4) || "/";
    target.search = requestUrl.search;

    const headers = new Headers(request.headers);
    headers.delete(GATEWAY_HEADER);
    if (!env.BACKEND_GATEWAY_TOKEN) {
      return apiError(500, "gateway_misconfigured", "The synthesis gateway is not configured.");
    }
    headers.set(GATEWAY_HEADER, env.BACKEND_GATEWAY_TOKEN);

    try {
      const originRequest = new Request(target, request);
      headers.forEach((value, name) => originRequest.headers.set(name, value));
      originRequest.headers.delete("host");
      const response = await fetchOrigin(originRequest);
      if ([502, 503, 504, 530].includes(response.status)) {
        return apiError(503, "backend_offline", "The synthesis backend is offline.");
      }
      return response;
    } catch {
      return apiError(503, "backend_offline", "The synthesis backend is offline.");
    }
  };
}

const handleRequest = createWorkerHandler();

export default {
  fetch(request: Request, env: Env): Promise<Response> {
    return handleRequest(request, env);
  },
};
