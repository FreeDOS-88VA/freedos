#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run the M18 host suite with its identity-pinned Unicorn wheel."""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import tempfile
import zipfile

import build_image

ROOT = Path(__file__).resolve().parents[2]


def extract_wheel(path: Path, destination: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            name = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (name.is_absolute() or ".." in name.parts or
                    stat.S_ISLNK(mode)):
                raise ValueError("unsafe path in pinned Unicorn wheel: " + item.filename)
            target = destination.joinpath(*name.parts)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as source, target.open("xb") as output:
                output.write(source.read())


def main() -> None:
    if sys.platform != "linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        raise SystemExit(
            "M18 host tests with Unicorn require Linux/x86_64; "
            "make m18-disk runs the same suite in its pinned Linux/amd64 container"
        )

    config = json.loads((ROOT / "config/m18/host-tooling.json").read_text())
    with tempfile.TemporaryDirectory(prefix="m18-host-tests-") as temporary:
        temporary_path = Path(temporary)
        inputs = temporary_path / "inputs"
        site = temporary_path / "site"
        inputs.mkdir()
        site.mkdir()
        wheel_record = build_image.get_wheel(config, inputs)
        wheel = inputs / wheel_record["filename"]
        extract_wheel(wheel, site)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(site)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        spec = config["unicorn_wheel"]
        check_version = (
            "from importlib.metadata import version; import unicorn; "
            "assert version('unicorn') == {!r}; "
            "assert unicorn.__version__ == {!r}"
        ).format(spec["version"], spec["version"])
        subprocess.run([sys.executable, "-B", "-c", check_version],
                       cwd=ROOT, env=environment, check=True)
        subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover",
             "-s", "tests/m18", "-p", "test_*.py", "-v"],
            cwd=ROOT, env=environment, check=True,
        )


if __name__ == "__main__":
    main()
