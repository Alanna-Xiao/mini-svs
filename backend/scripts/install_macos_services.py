#!/usr/bin/env python3
"""Install launchd jobs for the local backend and Cloudflare Tunnel."""

from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
from pathlib import Path


LABELS = ("com.mini-svs.backend", "com.mini-svs.tunnel")


def write_plist(path: Path, payload: dict[str, object]) -> None:
    with path.open("wb") as file:
        plistlib.dump(payload, file, sort_keys=False)


def main() -> None:
    repository = Path(__file__).resolve().parents[2]
    node = shutil.which("node")
    if node is None:
        raise SystemExit("Node.js was not found in PATH.")
    wrangler = repository / "frontend" / "node_modules" / "wrangler" / "bin" / "wrangler.js"
    if not wrangler.is_file():
        raise SystemExit("Wrangler is missing. Run npm install in frontend first.")

    agents = Path.home() / "Library" / "LaunchAgents"
    logs = Path.home() / "Library" / "Logs"
    agents.mkdir(parents=True, exist_ok=True)
    backend_log = str(logs / "mini-svs-backend.log")
    tunnel_log = str(logs / "mini-svs-tunnel.log")
    service_path = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

    jobs = {
        LABELS[0]: {
            "Label": LABELS[0],
            "ProgramArguments": [
                "/usr/bin/caffeinate",
                "-i",
                "/usr/bin/python3",
                str(repository / "backend" / "scripts" / "run_tunneled_backend.py"),
            ],
            "WorkingDirectory": str(repository),
            "EnvironmentVariables": {"PATH": service_path},
            "RunAtLoad": True,
            "KeepAlive": True,
            "ThrottleInterval": 10,
            "StandardOutPath": backend_log,
            "StandardErrorPath": backend_log,
        },
        LABELS[1]: {
            "Label": LABELS[1],
            "ProgramArguments": [
                node,
                str(wrangler),
                "tunnel",
                "run",
                "mini-svs-backend",
                "--log-level",
                "warn",
            ],
            "WorkingDirectory": str(repository / "frontend"),
            "EnvironmentVariables": {"PATH": service_path},
            "RunAtLoad": True,
            "KeepAlive": True,
            "ThrottleInterval": 10,
            "StandardOutPath": tunnel_log,
            "StandardErrorPath": tunnel_log,
        },
    }

    domain = f"gui/{os.getuid()}"
    for label, payload in jobs.items():
        path = agents / f"{label}.plist"
        subprocess.run(
            ["launchctl", "bootout", domain, str(path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        write_plist(path, payload)
        subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=True)
        subprocess.run(["launchctl", "kickstart", "-k", f"{domain}/{label}"], check=True)

    print("Installed and started mini-svs backend and tunnel services.")


if __name__ == "__main__":
    main()
