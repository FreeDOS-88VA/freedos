#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Normalize only nonsemantic TAR headers of the M20 parent Git export.

Git versions can encode a commit/PAX header differently. Preserve every
allowlisted file byte and executable mode; bind the rewritten archive's digest
as the *actual* parent build input and corresponding-source archive. This is
run with the pinned build image's Python, not a host packaging tool.
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path, PurePosixPath
import tarfile

PREFIXES = ("tools/m20/", "tests/m20/", "config/m20/")
SINGLES = {"COPYING", "LICENSE.md", "manifests/m20-components.lock.json",
           "manifests/toolchains.lock.json"}
ROOT_DIRS = {"config", "tools", "tests", "manifests"}


def allowed(name: str) -> bool:
    path = PurePosixPath(name)
    return (not path.is_absolute() and ".." not in path.parts and
            (name in SINGLES or name in ROOT_DIRS or
             name.rstrip("/") in {x.rstrip("/") for x in PREFIXES} or
             any(name.startswith(prefix) for prefix in PREFIXES)))


def records(archive: Path) -> dict[str, tuple[int, bytes | None]]:
    result = {}
    with tarfile.open(archive, "r:") as source:
        for item in source.getmembers():
            name = item.name.rstrip("/") if item.isdir() else item.name
            if (not allowed(name) or name in result or not (item.isfile() or item.isdir()) or
                    item.mode & ~0o777):
                raise ValueError("unsafe or repeated parent Git export member: " + name)
            data = source.extractfile(item).read() if item.isfile() else None
            result[name] = (0o755 if item.isdir() or item.mode & 0o111 else 0o644, data)
    if not result or not SINGLES.issubset(result) or not all(
            any(name.startswith(prefix) for name in result) for prefix in PREFIXES):
        raise ValueError("parent Git export lacks mandatory source roots")
    return result


def normalize(source: Path, output: Path, epoch: int) -> None:
    if epoch <= 0 or output.exists():
        raise ValueError("parent export epoch or output differs")
    entries = records(source)
    with tarfile.open(output, "w:", format=tarfile.USTAR_FORMAT) as archive:
        for name, (mode, data) in sorted(entries.items()):
            item = tarfile.TarInfo(name + "/" if data is None else name)
            item.uid = item.gid = 0
            item.uname = item.gname = ""
            item.mtime = epoch
            item.mode = mode
            item.type = tarfile.DIRTYPE if data is None else tarfile.REGTYPE
            item.size = 0 if data is None else len(data)
            archive.addfile(item, None if data is None else io.BytesIO(data))
    if records(output) != entries:
        output.unlink(missing_ok=True)
        raise ValueError("canonical parent archive changed files or modes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--epoch", type=int, required=True)
    args = parser.parse_args()
    normalize(args.source, args.output, args.epoch)


if __name__ == "__main__":
    main()
