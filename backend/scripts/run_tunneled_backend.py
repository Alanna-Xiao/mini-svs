#!/usr/bin/env python3
"""Run the local backend with the gateway token stored in macOS Keychain."""

from __future__ import annotations

import getpass
import os
import subprocess
from pathlib import Path


KEYCHAIN_SERVICE = "mini-svs-gateway-token"


def read_gateway_token() -> str:
    result = subprocess.run(
        [
            "/usr/bin/security",
            "find-generic-password",
            "-a",
            getpass.getuser(),
            "-s",
            KEYCHAIN_SERVICE,
            "-w",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    if not token:
        raise SystemExit(f"Keychain item {KEYCHAIN_SERVICE!r} is empty.")
    return token


def main() -> None:
    repository = Path(__file__).resolve().parents[2]
    uvicorn = repository / ".venv" / "bin" / "uvicorn"
    if not uvicorn.is_file():
        raise SystemExit("Backend environment is missing. Run the README setup first.")

    environment = os.environ.copy()
    environment["MINI_SVS_GATEWAY_TOKEN"] = read_gateway_token()
    os.execve(
        uvicorn,
        [
            str(uvicorn),
            "app.main:app",
            "--app-dir",
            str(repository / "backend"),
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--no-server-header",
        ],
        environment,
    )


if __name__ == "__main__":
    main()
