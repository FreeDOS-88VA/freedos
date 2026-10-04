#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check that the non-PC-88VA kernel build still equals the FreeDOS 1.4 baseline.

M20 adds PC-88VA support on top of FDOS kernel ke2043. Every PC-88VA change
to shared files must be confined to PC88VA builds, so the IBM PC target of
the M20 kernel commit must produce the same bytes as ke2043 itself. This
builds both from clean `git archive` exports with the kernel's own Linux
Open Watcom recipe (8086, FAT32, UPX disabled) in the pinned M20 toolchain
image and compares KERNEL.SYS, SYS.COM and COUNTRY.SYS byte for byte.

The kernel banner embeds the compile date, so both builds run in one
invocation. A mismatch is a defect of the PC-88VA port, not of the baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "4f7bdda16a84c416a82a2616aa67335ca4f2bd74"  # FDOS kernel ke2043
OUTPUTS = ("bin/kernel.sys", "bin/sys.com", "bin/country.sys")
CONFIG = "XNASM=nasm\nundefine XUPX\nXCPU=86\nXFAT=32\n"


def build(repo: Path, revision: str, tree: Path, image: str) -> dict[str, str]:
    tree = tree.resolve()
    tree.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(repo), "archive", revision],
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
    (tree / "config.mak").write_text(CONFIG)
    log = tree.with_suffix(".log")
    with log.open("wb") as stream:
        subprocess.run(["docker", "run", "--rm", "--platform", "linux/amd64",
                        "--network", "none", "-u", f"{os.getuid()}:{os.getgid()}",
                        "-v", f"{tree}:/work", "-w", "/work",
                        image, "-c", "make all COMPILER=owlinux"],
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    return {name: hashlib.sha256((tree / name).read_bytes()).hexdigest() for name in OUTPUTS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT / "components/fdkernel")
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--image", default="freedos-pc88va-m20:local")
    parser.add_argument("--output", type=Path, help="keep build trees and logs here")
    args = parser.parse_args()
    revision = subprocess.run(["git", "-C", str(args.repo), "rev-parse", args.revision],
                              check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "-C", str(args.repo), "merge-base", "--is-ancestor",
                    BASELINE, revision], check=True)
    work = Path(tempfile.mkdtemp(prefix="m20-pc-baseline-")) if args.output is None else args.output
    work.mkdir(parents=True, exist_ok=args.output is None)
    try:
        base = build(args.repo, BASELINE, work / "baseline", args.image)
        current = build(args.repo, revision, work / "current", args.image)
    finally:
        if args.output is None:
            shutil.rmtree(work, ignore_errors=True)
    record = {"baseline": BASELINE, "revision": revision, "baseline_sha256": base,
              "revision_sha256": current, "identical": base == current}
    print(json.dumps(record, indent=2))
    if base != current:
        raise SystemExit("non-PC-88VA kernel build differs from the FreeDOS 1.4 baseline")


if __name__ == "__main__":
    main()
