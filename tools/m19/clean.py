#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Remove only a marked, Git-excluded M19 intermediate build directory."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MARKER = "M19-generated-build-root-v1\n"


def clean(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("refusing to clean a symlink")
    path = path.resolve()
    if path == ROOT or ROOT not in path.parents:
        raise ValueError("M19 clean path must be below the repository root")
    if not subprocess.run(["git", "check-ignore", "-q", str(path / ".m19-probe")],
                          cwd=ROOT).returncode == 0:
        raise ValueError("M19 clean path is not Git-excluded")
    if not path.exists():
        print("M19 intermediate build root is already absent")
        return
    marker = path / ".m19-generated-root"
    if not path.is_dir() or marker.is_symlink():
        raise ValueError("refusing to remove a symlink or non-directory")
    if not marker.is_file():
        if any(path.iterdir()):
            raise ValueError("refusing to remove an unmarked or nonempty path")
        path.rmdir()
        print("Removed empty M19 intermediate root: " + str(path))
        return
    if marker.read_text(encoding="ascii") != MARKER:
        raise ValueError("refusing to remove an unmarked or mismatched path")
    shutil.rmtree(path)
    print("Removed generated M19 intermediates: " + str(path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=ROOT / "build/m19")
    args = parser.parse_args()
    clean(args.path)


if __name__ == "__main__":
    main()
