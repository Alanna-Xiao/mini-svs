import { describe, expect, it, vi } from "vitest";

import { createWorkerHandler } from "./index";

function environment() {
  return {
    ASSETS: { fetch: vi.fn(async () => new Response("asset")) },
    BACKEND_ORIGIN: "https://backend-origin.mini-svs.com",
    BACKEND_GATEWAY_TOKEN: "worker-secret",
  };
}

describe("worker gateway", () => {
  it("passes non-API requests to static assets", async () => {
    const env = environment();
    const response = await createWorkerHandler()(new Request("https://mini-svs.com/"), env);

    expect(await response.text()).toBe("asset");
    expect(env.ASSETS.fetch).toHaveBeenCalledOnce();
  });

  it("proxies API paths and replaces an untrusted gateway header", async () => {
    const originFetch = vi.fn(async (request: Request) => {
      expect(request.url).toBe("https://backend-origin.mini-svs.com/health?full=true");
      expect(request.headers.get("x-mini-svs-gateway-token")).toBe("worker-secret");
      return Response.json({ status: "ok" });
    });
    const request = new Request("https://mini-svs.com/api/health?full=true", {
      headers: { "x-mini-svs-gateway-token": "browser-value" },
    });

    const response = await createWorkerHandler(originFetch)(request, environment());

    expect(response.status).toBe(200);
    expect(originFetch).toHaveBeenCalledOnce();
  });

  it("returns a structured error while the local backend is offline", async () => {
    const response = await createWorkerHandler(async () => {
      throw new Error("offline");
    })(new Request("https://mini-svs.com/api/health"), environment());

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      error: { code: "backend_offline", message: "The synthesis backend is offline." },
    });
  });

  it("normalizes Cloudflare origin failures", async () => {
    const response = await createWorkerHandler(
      async () => new Response("Cloudflare error", { status: 530 }),
    )(new Request("https://mini-svs.com/api/health"), environment());

    expect(response.status).toBe(503);
    expect(await response.json()).toMatchObject({ error: { code: "backend_offline" } });
  });

  it("rejects API request bodies larger than 1 MB", async () => {
    const response = await createWorkerHandler()(
      new Request("https://mini-svs.com/api/render", {
        method: "POST",
        headers: { "content-length": "1000001" },
      }),
      environment(),
    );

    expect(response.status).toBe(413);
  });
});
