import react from "@vitejs/plugin-react";
import { execFileSync } from "node:child_process";
import { userInfo } from "node:os";
import { defineConfig } from "vitest/config";

function readGatewayToken(): string | undefined {
  try {
    return execFileSync(
      "/usr/bin/security",
      ["find-generic-password", "-a", userInfo().username, "-s", "mini-svs-gateway-token", "-w"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
    ).trim();
  } catch {
    return undefined;
  }
}

const gatewayToken = readGatewayToken();

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        headers: gatewayToken
          ? { "x-mini-svs-gateway-token": gatewayToken }
          : undefined,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}", "worker/**/*.test.ts"],
    setupFiles: "./src/test/setup.ts",
  },
});
