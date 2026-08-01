import { Container, getContainer } from "@cloudflare/containers";

type ContainerBinding = Parameters<typeof getContainer>[0];

interface Env {
  ASSETS: { fetch(request: Request): Promise<Response> };
  SYNTH_CONTAINER: ContainerBinding;
}

const MAX_API_BODY_BYTES = 1_000_000;

export class MiniSvsContainer extends Container {
  defaultPort = 8080;
  sleepAfter = "10m";
  enableInternet = false;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);
    }

    const contentLength = Number(request.headers.get("content-length") ?? 0);
    if (contentLength > MAX_API_BODY_BYTES) {
      return Response.json(
        { error: { code: "request_too_large", message: "API requests are limited to 1 MB." } },
        { status: 413 },
      );
    }

    url.pathname = url.pathname.slice(4) || "/";
    const containerRequest = new Request(url, request);
    return getContainer(env.SYNTH_CONTAINER, "mini-svs-primary").fetch(containerRequest);
  },
};
