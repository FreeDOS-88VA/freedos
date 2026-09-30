#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Audit the allowlisted M18 build inputs for privacy and release-source scope."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_COMPONENTS = {"fdkernel", "freecom", "country", "edlin", "jwasm"}
DOS_83 = re.compile(r"[A-Z0-9!#$%&'()@^_`{}~-]{1,8}(?:\.[A-Z0-9!#$%&'()@^_`{}~-]{1,3})?")
PRIVATE_NAMES = {".private-evidence", "pc88va-private-docs", "private", "roms"}


class AuditError(RuntimeError):
    pass


def verify(root: Path = DEFAULT_ROOT) -> None:
    root = root.resolve()
    for path in root.rglob("*"):
        if path.name in PRIVATE_NAMES or path.name.lower().endswith((".rom", ".d88", ".hdi", ".hdd", ".img")):
            raise AuditError("private or generated-media input is present: " + str(path.relative_to(root)))
    for directory in (root / "tools/m18", root / "tests/m18", root / "config/m18"):
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise AuditError("M18 build input is a symlink: " + str(path.relative_to(root)))

    lock_path = root / "manifests/m18-components.lock.json"
    lock = json.loads(lock_path.read_text(encoding="ascii"))
    if lock.get("milestone") != "M18" or lock.get("start_sha") != "d81bba18f0e4793d7165fb0acfdf7e229e160c83":
        raise AuditError("M18 start/source lock identity differs")
    components = {item.get("name"): item for item in lock.get("components", [])}
    if set(components) != REQUIRED_COMPONENTS:
        raise AuditError("M18 public component set differs")
    for name, item in components.items():
        if (not re.fullmatch(r"[0-9a-f]{40}", item.get("commit", "")) or
                not re.fullmatch(r"[0-9a-f]{64}", item.get("source_archive_sha256", "")) or
                not (root / item.get("path", "")).is_dir()):
            raise AuditError("M18 component input is absent or has an invalid source identity: " + name)

    packages = json.loads((root / "config/m18/packages.json").read_text(encoding="ascii"))
    if packages.get("milestone") != "M18" or not isinstance(packages.get("packages"), list):
        raise AuditError("M18 package manifest configuration is malformed")
    package_ids = {item.get("id") for item in packages["packages"]}
    if package_ids != {"fdkernel", "freecom", "country", "edlin", "more",
                       "maintenance", "memmap", "jwasm", "starter-material"}:
        raise AuditError("M18 mandatory package set differs")
    for item in packages["packages"]:
        if item.get("source_lock") and item["source_lock"] not in components:
            raise AuditError("M18 package refers to an unpinned component")
        for filename in item.get("files", []):
            if not isinstance(filename, str) or not DOS_83.fullmatch(filename):
                raise AuditError("M18 disk path is not uppercase DOS 8.3: " + str(filename))

    payload = root / "config/m18/payload"
    for path in payload.iterdir():
        if path.is_file() and not path.read_bytes().isascii():
            raise AuditError("M18 release text is not ASCII: " + path.name)
    config = (root / "config/m18/CONFIG.SYS").read_text(encoding="ascii")
    if "SET PATH=A:\\" not in config or "PC88VA_LOADSEG=1000" not in config:
        raise AuditError("M18 normal DOS path or accepted loader selection is missing")
    print("M18 public source/privacy audit: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    verify(args.root)


if __name__ == "__main__":
    main()
