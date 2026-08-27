# Deployment

## Topology

The free deployment uses Cloudflare for the public edge and the author's Mac for synthesis:

```text
Browser
  -> mini-svs.com Cloudflare Worker
  -> backend-origin.mini-svs.com Cloudflare Tunnel
  -> 127.0.0.1:8000 FastAPI
  -> local voicebank, instruments, engine, and output
```

The Worker serves built frontend assets and proxies `/api/*`. It strips the `/api` prefix, replaces any browser-supplied gateway header, and forwards the request to the Tunnel origin. Static editing remains available while the Mac is offline; synthesis calls return a structured `503 backend_offline` response.

## Security Boundary

- `BACKEND_GATEWAY_TOKEN` is a Cloudflare Worker secret, never a public Worker variable.
- The same value is stored as `mini-svs-gateway-token` in macOS Keychain and exposed to FastAPI only as `MINI_SVS_GATEWAY_TOKEN` at process startup.
- The browser must never receive this token.
- Raw voice recordings, processed voicebank samples, SoundFonts, model weights, and rendered output remain local and ignored by git.
- User registration is deferred. The gateway token authenticates the Worker service, not individual users.

## Local Services

Two launchd jobs keep the synthesis path running after login:

- `com.mini-svs.backend`: starts Uvicorn on loopback and prevents idle sleep while running.
- `com.mini-svs.tunnel`: runs the named `mini-svs-backend` Cloudflare Tunnel.

The jobs restart after crashes. They cannot keep a Mac reachable while it is shut down, logged out, disconnected from the network, or sleeping with the lid closed.

## Limits

- API request bodies are limited to 1 MB by the Worker gateway.
- A single local backend is intended for low-volume demo use, not concurrent public rendering at scale.
- Long synchronous renders can hit Cloudflare or browser connection timeouts. A future release should move rendering to asynchronous jobs with polling.
- Generated output is stored on the Mac and is unavailable whenever the backend is offline.
- The free Worker plan's request and CPU quotas apply to the gateway.

## Provisioning

1. Create the named `mini-svs-backend` Tunnel and map `backend-origin.mini-svs.com` to `http://127.0.0.1:8000`.
2. Generate one high-entropy gateway token, store it in macOS Keychain, and upload the same value with `wrangler secret put BACKEND_GATEWAY_TOKEN`.
3. Run `python3 backend/scripts/install_macos_services.py` to install the launchd jobs.
4. Run `npm run deploy` in `frontend/` to publish the Worker and frontend assets.

Tunnel routing and Worker deployment are infrastructure operations. They are intentionally separate from voicebank, engine, and output implementation.
