#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build pinned FreeDOS FIND for 8086 DOS with Open Watcom 1.9.

The FDOS find repository refers to its kitten and tnyprntf libraries as Git
submodules, which `git archive` does not include. M20 pins them as separate
components and stages them where find's sources expect them (`find/kitten`,
`find/tnyprntf`). Compiler options follow find's own `build.sh` Watcom
cross-compile settings, with the 8086 target stated explicitly and without
UPX compression.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

OPTIONS = ["-q", "-bt=DOS", "-bcl=DOS", "-D__MSDOS__", "-zp1", "-ms", "-0", "-lr"]
SOURCES = {"find": ("src/find.c", "src/find_str.c", "src/find_str.h", "doc/copying"),
           "kitten": ("kitten.c", "kitten.h", "LICENSE"),
           "tnyprntf": ("tnyprntf.c", "tnyprntf.h", "LICENSE")}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_mz(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 28:
        raise ValueError("FIND MZ header is truncated")
    magic, last_page, pages, relocs, header_paras, minalloc, maxalloc = struct.unpack_from("<7H", data)
    if magic != 0x5A4D or pages == 0 or last_page > 511:
        raise ValueError("FIND output is not a valid MZ executable")
    declared = (pages - 1) * 512 + last_page if last_page else pages * 512
    if declared != len(data) or header_paras * 16 > declared:
        raise ValueError("FIND MZ header and file extents disagree")
    return {"file_size_bytes": len(data), "file_sha256": hashlib.sha256(data).hexdigest(),
            "mz_header_bytes": header_paras * 16, "relocation_count": relocs,
            "mz_minimum_extra_paragraphs": minalloc}


def build(sources: dict[str, Path], output: Path, revisions: dict[str, str]) -> dict[str, object]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError("FIND output directory must not already exist")
    for name, files in SOURCES.items():
        for relative in files:
            if not (sources[name] / relative).is_file():
                raise ValueError(f"pinned {name} source is missing {relative}")
    watcom = Path(os.environ.get("WATCOM", ""))
    compiler = shutil.which(os.environ.get("WCL", "wcl"))
    if not watcom.is_dir() or compiler is None:
        raise RuntimeError("the pinned Open Watcom installation and wcl are required")
    output.mkdir(parents=True)
    staged = output / "find"
    shutil.copytree(sources["find"], staged, ignore=shutil.ignore_patterns(".git"))
    for library in ("kitten", "tnyprntf"):
        target = staged / library
        if target.exists():
            if any(target.iterdir()):
                raise ValueError(f"find source unexpectedly contains {library} files")
            target.rmdir()
        shutil.copytree(sources[library], target, ignore=shutil.ignore_patterns(".git"))
    env = os.environ.copy()
    env["INCLUDE"] = str(watcom / "h")
    src = staged / "src"
    subprocess.run([compiler, *OPTIONS, "-fo=kitten.obj", "-c", "../kitten/kitten.c"],
                   cwd=src, env=env, check=True)
    subprocess.run([compiler, *OPTIONS, "-fo=tnyprntf.obj", "-c", "../tnyprntf/tnyprntf.c"],
                   cwd=src, env=env, check=True)
    subprocess.run([compiler, *OPTIONS, "-fm=find.map", "-fe=find.exe", "find.c", "find_str.c",
                    "tnyprntf.obj", "kitten.obj"], cwd=src, env=env, check=True)
    record = check_mz(src / "find.exe")
    record.update({
        "source_revisions": revisions,
        "source_files": {f"{name}/{relative}": sha256(sources[name] / relative)
                         for name, files in SOURCES.items() for relative in files},
        "toolchain": "Open Watcom 1.9; identities are verified by the M20 toolchain lock",
        "compiler_options": OPTIONS,
        "upx": False,
        "messages": "built-in English; kitten NLS catalogs are not installed",
        "license": "FIND GPL-2.0-or-later; tnyprntf GPL-2.0; kitten LGPL-2.1",
    })
    shutil.copy2(src / "find.exe", output / "FIND.EXE")
    (output / "find-build.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                                            encoding="ascii")
    print("Built FIND.EXE: {} bytes".format(record["file_size_bytes"]))
    return record
