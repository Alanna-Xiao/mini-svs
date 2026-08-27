#!/usr/bin/env python3
"""Install the pinned DiffSinger toolchain and starter vocoder locally."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


REPOSITORY = "https://github.com/openvpi/DiffSinger.git"
REVISION = "ee7463f551dac8f5f36caa30e4e61fdbbed6d3cd"
VOCODER_URL = (
    "https://github.com/openvpi/vocoders/releases/download/"
    "nsf-hifigan-44.1k-hop512-128bin-2024.02/"
    "nsf_hifigan_44.1k_hop512_128bin_2024.02.zip"
)
VOCODER_SHA256 = "2f41cc179ef9d76f0b4cf1f01abd18af6f32fa7dfad66bfa65a4fcf54829f957"


def run(*command: str, cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def download(url: str, destination: Path) -> None:
    if destination.exists():
        print(f"Using existing download: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    print(f"Downloading {url}", flush=True)
    urllib.request.urlretrieve(url, temporary)
    temporary.replace(destination)


def verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch for {path}: expected {expected}, got {actual}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / ".ai",
        help="Local installation directory (default: <repo>/.ai)",
    )
    parser.add_argument(
        "--skip-dependencies",
        action="store_true",
        help="Clone DiffSinger and install the vocoder without pip dependencies",
    )
    return parser.parse_args()


def main() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("DiffSinger requires Python 3.10 or newer.")

    args = parse_args()
    root = args.root.resolve()
    source = root / "DiffSinger"
    environment = root / "venv"
    downloads = root / "downloads"

    root.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        run("git", "clone", REPOSITORY, str(source))
    run("git", "fetch", "origin", REVISION, cwd=source)
    run("git", "checkout", "--detach", REVISION, cwd=source)

    if not environment.exists():
        run(sys.executable, "-m", "venv", str(environment))
    python = environment / "bin" / "python"

    if not args.skip_dependencies:
        run(
            str(python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools<81",
            "wheel",
        )
        run(str(python), "-m", "pip", "install", "torch>=2.4")
        run(str(python), "-m", "pip", "install", "-r", str(source / "requirements.txt"))

    archive = downloads / Path(VOCODER_URL).name
    download(VOCODER_URL, archive)
    verify_sha256(archive, VOCODER_SHA256)
    checkpoint_dir = source / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    marker = checkpoint_dir / ".mini-svs-vocoder-installed"
    if not marker.exists():
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(checkpoint_dir)
        marker.write_text(VOCODER_URL + "\n", encoding="ascii")

    print("\nDiffSinger installation ready:")
    print(f"  source:  {source}")
    print(f"  python:  {python}")
    print(f"  vocoder: {checkpoint_dir}")
    print("An author acoustic model will be added here after training data is ready.")


if __name__ == "__main__":
    main()
