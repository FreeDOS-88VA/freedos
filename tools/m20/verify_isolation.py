#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail closed on cross-milestone M00-M19 runtime source dependencies."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
MILESTONE_PARENTS = ("tools", "config", "tests", "containers")
# Historical milestone directories include suffixed revisions such as m07r2.
HISTORICAL_NAME = re.compile(r"m(?:0[0-9]|1[0-9])[a-z0-9]*")
# Files without a suffix (for example Dockerfile) are scanned as well.
SCAN_SUFFIXES = {"", ".py", ".sh", ".json", ".c", ".h", ".asm", ".inc", ".bat",
                 ".md", ".txt", ".doc", ".sys", ".mak", ".wc", ".yml", ".yaml"}
RUNTIME_PATTERNS = (
    re.compile(r"(?:from|import)\s+(?:tools\.)?m(?:0[0-9]|1[0-9])[a-z0-9]*(?:\.|\s|$)"),
    re.compile(r"(?:tools|config|tests|containers)/m(?:0[0-9]|1[0-9])[a-z0-9]*"
               r"(?:[/'\"\s),;:]|$)", re.MULTILINE),
    re.compile(r"sys\.path[^\n]*m(?:0[0-9]|1[0-9])"),
)


class IsolationError(RuntimeError):
    pass


def verify(root: Path = DEFAULT_ROOT) -> None:
    root = root.resolve()
    required = ("tools/m20", "tests/m20", "config/m20",
                "manifests/m20-components.lock.json",
                "manifests/toolchains.lock.json", "components/fdkernel",
                "components/freecom", "components/country", "components/edlin",
                "components/jwasm")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from component_set import locked_names
    if (root / "manifests/m20-components.lock.json").is_file():
        required = required + tuple("components/" + name for name in locked_names(root)
                                    if "components/" + name not in required)
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        raise IsolationError("M20 source export is missing: " + ", ".join(missing))
    for parent in MILESTONE_PARENTS:
        directory = root / parent
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if HISTORICAL_NAME.fullmatch(path.name):
                raise IsolationError("M20 source export contains forbidden milestone input: " +
                                     parent + "/" + path.name)
    scanned = (root / "tools/m20", root / "tests/m20", root / "config/m20")
    for directory in scanned:
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise IsolationError("M20 runtime input is a symlink: " + str(path.relative_to(root)))
            if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise IsolationError("M20 source input is not UTF-8: " + str(path.relative_to(root))) from exc
            for pattern in RUNTIME_PATTERNS:
                if pattern.search(text):
                    raise IsolationError("M20 runtime source references an earlier milestone: " +
                                         str(path.relative_to(root)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    verify(args.root)
    print("M20 milestone isolation: PASS")


if __name__ == "__main__":
    main()
