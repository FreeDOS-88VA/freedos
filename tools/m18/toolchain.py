#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build or verify the milestone-local Linux/amd64 Open Watcom environment."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IMAGE = "freedos-pc88va-m18:local"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def docker_json(*args: str) -> dict:
    return json.loads(subprocess.check_output(args, cwd=ROOT, text=True))[0]


def verify_image(image: str, lock: dict) -> str:
    info = docker_json("docker", "image", "inspect", image)
    if (info.get("Os"), info.get("Architecture")) != ("linux", "amd64"):
        raise ValueError("M18 toolchain must be a Linux/amd64 image")
    check = r'''import hashlib,json,pathlib,sys
for item in json.loads(sys.stdin.read()):
 p=pathlib.Path('/opt/openwatcom-1.9')/item['path']
 data=p.read_bytes()
 assert len(data)==item['size'] and hashlib.sha256(data).hexdigest()==item['sha256'], item['name']
'''
    subprocess.run(
        ["docker", "run", "--rm", "-i", "--platform", "linux/amd64",
         "--network", "none", "--entrypoint", "python3", info["Id"], "-c", check],
        input=json.dumps(lock["open_watcom"]["host_tools"]).encode(), check=True,
    )
    return info["Id"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    lock = json.loads((ROOT / "manifests/toolchains.lock.json").read_text())["canonical"]
    dockerfile = ROOT / "tools/m18/toolchain/Dockerfile"
    text = dockerfile.read_text(encoding="ascii")
    if lock["base_image"]["amd64_manifest_digest"] not in text:
        raise ValueError("M18 Dockerfile base differs from the shared toolchain lock")
    if lock["open_watcom"]["release"] != "Open Watcom 1.9":
        raise ValueError("M18 requires the locked final Open Watcom 1.9 release")

    exists = subprocess.run(["docker", "image", "inspect", args.image],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL).returncode == 0
    if exists and not args.rebuild:
        identity = verify_image(args.image, lock)
        print("Verified M18 toolchain image: " + identity)
        return

    cache = ROOT / "build/m18-toolchain-download"
    cache.mkdir(parents=True, exist_ok=True)
    ow = lock["open_watcom"]
    archive = cache / ow["package"]
    if not archive.exists():
        partial = archive.with_suffix(".part")
        try:
            with urllib.request.urlopen(ow["official_github_url"]) as response, partial.open("wb") as target:
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
            partial.replace(archive)
        finally:
            partial.unlink(missing_ok=True)
    data = archive.read_bytes()
    if len(data) != ow["asset_size"] or sha256(data) != ow["sha256"]:
        raise ValueError("Downloaded Open Watcom archive differs from the shared lock")

    subprocess.run(
        ["docker", "buildx", "build", "--load", "--platform", "linux/amd64",
         "--build-context", "watcom=" + str(cache),
         "--build-arg", "APT_SNAPSHOT=" + lock["apt"]["snapshot_id"],
         "--build-arg", "OW_PACKAGE_SIZE=" + str(ow["asset_size"]),
         "--build-arg", "OW_PUBLISHER_MD5=" + ow["publisher_md5"],
         "--build-arg", "OW_PACKAGE_SHA256=" + ow["sha256"],
         "-t", args.image, str(dockerfile.parent)], check=True,
    )
    identity = verify_image(args.image, lock)
    print("Built and verified M18 toolchain image: " + identity)


if __name__ == "__main__":
    main()
