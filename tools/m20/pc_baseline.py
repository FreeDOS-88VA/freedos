#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check that non-PC-88VA kernel, FreeCOM and forked-utility builds equal FreeDOS 1.4.

M20 adds PC-88VA support on top of FDOS kernel ke2043. Every PC-88VA change
to shared files must be confined to PC88VA builds, so the IBM PC target of
the M20 kernel commit must produce the same bytes as ke2043 itself. This
builds both from clean `git archive` exports with the kernel's own Linux
Open Watcom recipe (8086, FAT32, UPX disabled) in the pinned M20 toolchain
image and compares KERNEL.SYS, SYS.COM and COUNTRY.SYS byte for byte.

The kernel banner embeds the compile date, so both builds run in one
invocation. FreeCOM is checked the same way against FDOS com086 with its own
default build (Open Watcom, XMS swap, English); COMMAND.COM may differ only
inside its embedded __DATE__/__TIME__ strings. Forked utilities (lock entries
with an upstream_base_commit) are built without their PC88VA defines from the
upstream base and from the pinned fork commit and must be byte-identical; a
fork whose upstream base cannot be built by the pinned tools must instead
reproduce its recorded FreeDOS 1.4 package binary. A mismatch is a defect of
the PC-88VA port, not of the baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "4f7bdda16a84c416a82a2616aa67335ca4f2bd74"  # FDOS kernel ke2043
FREECOM_BASELINE = "f1b8f4f464eae5a70348b6d362484d733d45c427"  # FDOS freecom com086
TIMESTAMP = re.compile(rb"[A-Z][a-z]{2} [ 0-9][0-9] [0-9]{4}( [0-9]{2}:[0-9]{2}:[0-9]{2})?")
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


def build_freecom(repo: Path, revision: str, tree: Path, image: str) -> bytes:
    tree = tree.resolve()
    tree.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(repo), "archive", revision],
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
    with tree.with_suffix(".log").open("wb") as stream:
        subprocess.run(["docker", "run", "--rm", "--platform", "linux/amd64",
                        "--network", "none", "-u", f"{os.getuid()}:{os.getgid()}",
                        "-v", f"{tree}:/work", "-w", "/work",
                        image, "-c", "bash build.sh wc english"],
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    return (tree / "command.com").read_bytes()


def same_except_timestamps(a: bytes, b: bytes) -> bool:
    if len(a) != len(b):
        return False
    masked = set()
    for data in (a, b):
        for match in TIMESTAMP.finditer(data):
            masked.update(range(match.start(), match.end()))
    return all(a[i] == b[i] or i in masked for i in range(len(a)))


def utility_baselines(root: Path, work: Path, image: str) -> dict[str, bool]:
    """Build forked utilities without PC88VA from their upstream base and pin."""
    import sys
    sys.path.insert(0, str(root / "tools/m20"))
    from utilities.build_tools import TOOLS
    lock = json.loads((root / "manifests/m20-components.lock.json").read_text())
    commits = {item["name"]: item["commit"] for item in lock["components"]}
    forks = [item for item in lock["components"]
             if item.get("upstream_base_commit") and item["name"] in TOOLS]
    results: dict[str, bool] = {}
    for item in forks:
        name = item["name"]
        spec = TOOLS[name]
        libraries = [spec["kitten"], "tnyprntf"] if spec.get("kitten") else []
        outputs = {}
        release = item.get("release_binary")
        # A fork that only makes old source build with the pinned tools has no
        # buildable upstream base; it must reproduce the FreeDOS 1.4 binary.
        revisions = ((("current", commits[name]),) if release else
                     (("base", item["upstream_base_commit"]), ("current", commits[name])))
        for label, revision in revisions:
            components = (work / ("utility-" + label) / name / "components").resolve()
            for component, rev in [(name, revision)] + [(lib, commits[lib]) for lib in libraries]:
                target = components / component
                target.mkdir(parents=True)
                archive = subprocess.run(["git", "-C", str(root / "components" / component),
                                          "archive", rev], check=True, capture_output=True).stdout
                subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
            out = components.parent / "out"
            with (components.parent / "build.log").open("wb") as stream:
                subprocess.run(["docker", "run", "--rm", "--platform", "linux/amd64",
                                "--network", "none", "-u", f"{os.getuid()}:{os.getgid()}",
                                "-v", f"{root.resolve()}:/src:ro", "-v", f"{components.parent}:/w",
                                "-w", "/w", image, "-c",
                                "python3 -B /src/tools/m20/utilities/build_tools.py "
                                "--components /w/components --output /w/out --no-platform " + name],
                               stdout=stream, stderr=subprocess.STDOUT, check=True)
            outputs[label] = (out / spec["output"]).read_bytes()
        if release:
            results[name] = hashlib.sha256(outputs["current"]).hexdigest() == release["sha256"]
        else:
            results[name] = outputs["base"] == outputs["current"]
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT / "components/fdkernel")
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--freecom-repo", type=Path, default=ROOT / "components/freecom")
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
        freecom = subprocess.run(["git", "-C", str(args.freecom_repo), "rev-parse", "HEAD"],
                                 check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "-C", str(args.freecom_repo), "merge-base", "--is-ancestor",
                        FREECOM_BASELINE, freecom], check=True)
        shell_base = build_freecom(args.freecom_repo, FREECOM_BASELINE,
                                   work / "freecom-baseline", args.image)
        shell_current = build_freecom(args.freecom_repo, freecom,
                                      work / "freecom-current", args.image)
        utilities = utility_baselines(ROOT, work, args.image)
    finally:
        if args.output is None:
            shutil.rmtree(work, ignore_errors=True)
    shell_same = same_except_timestamps(shell_base, shell_current)
    record = {"baseline": BASELINE, "revision": revision, "baseline_sha256": base,
              "revision_sha256": current, "identical": base == current,
              "freecom_baseline": FREECOM_BASELINE, "freecom_revision": freecom,
              "freecom_identical_except_timestamps": shell_same,
              "forked_utilities_identical_without_pc88va": utilities}
    print(json.dumps(record, indent=2))
    if base != current:
        raise SystemExit("non-PC-88VA kernel build differs from the FreeDOS 1.4 baseline")
    if not shell_same:
        raise SystemExit("non-PC-88VA FreeCOM build differs from the FreeDOS 1.4 baseline")
    if not utilities or not all(utilities.values()):
        raise SystemExit("a forked utility built without PC88VA differs from its FreeDOS 1.4 source")


if __name__ == "__main__":
    main()
