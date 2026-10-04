#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Audit the allowlisted M20 build inputs for privacy and release-source scope."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
DOS_83 = re.compile(r"[A-Z0-9!#$%&'()@^_`{}~-]{1,8}(?:\.[A-Z0-9!#$%&'()@^_`{}~-]{1,3})?")
PRIVATE_NAMES = {".private-evidence", "pc88va-private-docs", "private", "roms"}


class AuditError(RuntimeError):
    pass


def audit_data_disk(root, components, kind, utility):
    """A data disk configuration names pinned components, DOS names and notices."""
    if utility.get("milestone") != "M20" or not isinstance(utility.get("packages"), list):
        raise AuditError("M20 " + kind + " disk configuration is malformed")
    for item in utility["packages"]:
        if not item.get("source_locks") or any(name not in components for name in item["source_locks"]):
            raise AuditError("M20 " + kind + " package refers to an unpinned component")
        for filename in item.get("files", []):
            if not isinstance(filename, str) or not DOS_83.fullmatch(filename):
                raise AuditError("M20 " + kind + " disk path is not uppercase DOS 8.3: " + str(filename))
    for filename in list(utility.get("notices", {})) + ["README.TXT"]:
        if not DOS_83.fullmatch(filename):
            raise AuditError("M20 " + kind + " notice path is not uppercase DOS 8.3: " + filename)
    for notice in utility.get("notices", {}).values():
        relative = notice if isinstance(notice, str) else notice.get("source", "")
        if not (root / relative).is_file():
            raise AuditError("M20 " + kind + " notice source is missing: " + str(relative))
    if not (root / utility["readme"]).read_bytes().isascii():
        raise AuditError("M20 " + kind + " README is not ASCII")


def verify(root: Path = DEFAULT_ROOT) -> None:
    root = root.resolve()
    for path in root.rglob("*"):
        if path.name in PRIVATE_NAMES or path.name.lower().endswith((".rom", ".d88", ".hdi", ".hdd", ".img")):
            raise AuditError("private or generated-media input is present: " + str(path.relative_to(root)))
    for directory in (root / "tools/m20", root / "tests/m20", root / "config/m20"):
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise AuditError("M20 build input is a symlink: " + str(path.relative_to(root)))

    lock_path = root / "manifests/m20-components.lock.json"
    lock = json.loads(lock_path.read_text(encoding="ascii"))
    if lock.get("milestone") != "M20" or lock.get("start_sha") != "ba868e2e33447fe5fcb3a2bed0711464f7968d82":
        raise AuditError("M20 start/source lock identity differs")
    components = {item.get("name"): item for item in lock.get("components", [])}
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from component_set import locked_names
    try:
        if set(components) != set(locked_names(root)):
            raise AuditError("M20 public component set differs")
    except ValueError as exc:
        raise AuditError("M20 public component set differs") from exc
    for name, item in components.items():
        if (not re.fullmatch(r"[0-9a-f]{40}", item.get("commit", "")) or
                not re.fullmatch(r"[0-9a-f]{64}", item.get("source_archive_sha256", "")) or
                not (root / item.get("path", "")).is_dir()):
            raise AuditError("M20 component input is absent or has an invalid source identity: " + name)

    packages = json.loads((root / "config/m20/packages.json").read_text(encoding="ascii"))
    if packages.get("milestone") != "M20" or not isinstance(packages.get("packages"), list):
        raise AuditError("M20 package manifest configuration is malformed")
    package_ids = {item.get("id") for item in packages["packages"]}
    if package_ids != {"fdkernel", "freecom", "country", "edlin", "more",
                       "maintenance", "memmap", "jwasm", "starter-material"}:
        raise AuditError("M20 mandatory package set differs")
    for item in packages["packages"]:
        if item.get("source_lock") and item["source_lock"] not in components:
            raise AuditError("M20 package refers to an unpinned component")
        for filename in item.get("files", []):
            if not isinstance(filename, str) or not DOS_83.fullmatch(filename):
                raise AuditError("M20 disk path is not uppercase DOS 8.3: " + str(filename))

    from data_disks import DATA_DISKS
    for kind, entry in DATA_DISKS.items():
        audit_data_disk(root, components, kind,
                        json.loads((root / entry["config"]).read_text(encoding="ascii")))

    payload = root / "config/m20/payload"
    for path in payload.iterdir():
        if path.is_file() and not path.read_bytes().isascii():
            raise AuditError("M20 release text is not ASCII: " + path.name)
    config = (root / "config/m20/CONFIG.SYS").read_text(encoding="ascii")
    if "SET PATH=A:\\" not in config or "PC88VA_LOADSEG=1000" not in config:
        raise AuditError("M20 normal DOS path or accepted loader selection is missing")
    print("M20 public source/privacy audit: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    verify(args.root)


if __name__ == "__main__":
    main()
