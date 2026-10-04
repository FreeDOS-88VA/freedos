#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build pinned FreeDOS 1.4 utilities for 8086 DOS with Open Watcom 1.9 / NASM.

Each entry of TOOLS reproduces the program's own Open Watcom or NASM build
settings (its build.sh, Makefile or make.bat), with the 8086 target stated
explicitly for C programs and without UPX compression. Programs whose Git
repository refers to kitten/tnyprntf submodules get those libraries from
separately pinned components (git archive omits submodules), staged where the
program's sources expect them.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

# C programs built from src/ with kitten and tnyprntf objects.
KITTEN_C = "kitten"
TOOLS: dict[str, dict] = {
    "find": {"kind": KITTEN_C, "kitten": "kitten", "model": "-ms", "pack": True,
             "sources": ["find.c", "find_str.c"], "output": "FIND.EXE", "link": "find.exe"},
    "sort": {"kind": KITTEN_C, "kitten": "kitten-3b9947f", "model": "-ms", "pack": True,
             "sources": ["sort.c"], "output": "SORT.EXE", "link": "sort.exe",
             "objects": ["kitten.obj", "tnyprntf.obj"]},
    # MOVE overflows Open Watcom's default 2 KiB stack (checked on PC and VA);
    # an 8 KiB stack is a build setting only, no source change.
    "move": {"kind": KITTEN_C, "kitten": "kitten-3b9947f", "model": "-ms", "pack": False,
             "sources": ["move.c", "movedir.c", "misc.c"], "output": "MOVE.EXE", "link": "move.exe",
             "link_options": ["-k8192"]},
    # label's build.sh compiles everything in one wcl invocation.
    "label": {"kind": "single-wcl", "kitten": "kitten-3b9947f", "directory": "src",
              "options": ["-bt=DOS", "-bcl=DOS", "-D__MSDOS__", "-zp1", "-ms", "-0", "-lr"],
              "sources": ["label.c", "../kitten/kitten.c", "../tnyprntf/tnyprntf.c"],
              "output": "LABEL.EXE", "link": "label.exe"},
    # xcopy carries its own kitten copy; options are its makefile's WATCOM set.
    "xcopy": {"kind": "single-wcl", "directory": "source",
              "options": ["-oas", "-bt=DOS", "-zp1", "-ms", "-0", "-wx", "-we", "-zq",
                          "-fm", "-k12288"],
              "sources": ["xcopy.c", "kitten.c", "prf.c"], "output": "XCOPY.EXE",
              "link": "xcopy.exe"},
    # Fork with an Open Watcom portability fix (carry flag test); FreeDOS 1.4
    # shipped a Borland build, so there is no byte baseline (see the lock).
    "fc": {"kind": KITTEN_C, "kitten": "kitten", "model": "-mc", "pack": True,
           "sources": ["fc.c", "fctools.c"], "output": "FC.EXE", "link": "fc.exe"},
    # Project forks: PC88VA builds select DOS replacements for PC BIOS use;
    # builds without the define equal the FreeDOS 1.4 source (checked by
    # tools/m20/pc_baseline.py).
    "choice": {"kind": KITTEN_C, "kitten": "kitten", "model": "-ms", "pack": True,
               "sources": ["choice.c"], "output": "CHOICE.EXE", "link": "choice.exe",
               "platform_defines": ["-DPC88VA"]},
    "deltree": {"kind": "nasm", "directory": ".",
                "command": ["-o", "deltree.com", "deltree.asm"],
                "output": "DELTREE.COM", "link": "deltree.com",
                "platform_defines": ["-DPC88VA"]},
    # Fork with a NASM 2.x syntax fix; the output equals the FreeDOS 1.4
    # package binary (checked by tools/m20/pc_baseline.py).
    "comp": {"kind": "nasm", "directory": ".",
             "command": ["comp.asm", "-o", "comp.com", "-O", "2"],
             "output": "COMP.COM", "link": "comp.com"},
    "append": {"kind": "nasm", "directory": "source",
               "command": ["-dNEW_NASM", "-fbin", "append.asm", "-o", "append.exe"],
               "output": "APPEND.EXE", "link": "append.exe"},
    "nlsfunc": {"kind": "nasm", "directory": ".",
                "command": ["-dNEW_NASM", "-fbin", "nlsfunc.asm", "-o", "nlsfunc.exe"],
                "output": "NLSFUNC.EXE", "link": "nlsfunc.exe"},
    "devload": {"kind": "nasm", "directory": ".",
                "command": ["-O5", "-o", "devload.com", "devload.asm"],
                "output": "DEVLOAD.COM", "link": "devload.com"},
}
C_BASE = ["-q", "-bt=DOS", "-bcl=DOS", "-D__MSDOS__"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_program(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    record = {"file_size_bytes": len(data), "file_sha256": hashlib.sha256(data).hexdigest()}
    if path.suffix.lower() == ".com":
        if not data or len(data) > 0xFF00:
            raise ValueError(path.name + " is not a valid COM program")
        record["format"] = "COM"
        return record
    if len(data) < 28:
        raise ValueError(path.name + " MZ header is truncated")
    magic, last_page, pages, relocs, header_paras = struct.unpack_from("<5H", data)
    declared = (pages - 1) * 512 + last_page if last_page else pages * 512
    if magic != 0x5A4D or pages == 0 or last_page > 511 or declared != len(data) \
            or header_paras * 16 > declared:
        raise ValueError(path.name + " is not a consistent MZ executable")
    record.update(format="MZ", relocation_count=relocs, mz_header_bytes=header_paras * 16)
    return record


def stage(name: str, spec: dict, components: Path, output: Path) -> Path:
    tree = output / name
    shutil.copytree(components / name, tree, ignore=shutil.ignore_patterns(".git"))
    if spec.get("kitten"):
        for library, component in (("kitten", spec["kitten"]), ("tnyprntf", "tnyprntf")):
            target = tree / library
            if target.exists():
                if any(target.iterdir()):
                    raise ValueError(f"{name} source unexpectedly contains {library} files")
                target.rmdir()
            shutil.copytree(components / component, target, ignore=shutil.ignore_patterns(".git"))
    return tree


def build_one(name: str, components: Path, output: Path, env: dict,
              platform: bool = True) -> dict[str, object]:
    spec = TOOLS[name]
    tree = stage(name, spec, components, output)
    kind = spec["kind"]
    defines = spec.get("platform_defines", []) if platform else []
    if kind == KITTEN_C:
        src = tree / "src"
        options = C_BASE + defines + (["-zp1"] if spec["pack"] else []) + [spec["model"], "-0", "-lr"]
        commands = [["wcl", *options, "-fo=kitten.obj", "-c", "../kitten/kitten.c"],
                    ["wcl", *options, "-fo=tnyprntf.obj", "-c", "../tnyprntf/tnyprntf.c"],
                    ["wcl", *options, *spec.get("link_options", []), "-fe=" + spec["link"], *spec["sources"],
                     *spec.get("objects", ["tnyprntf.obj", "kitten.obj"])]]
    elif kind == "single-wcl":
        src = tree / spec["directory"]
        commands = [["wcl", *spec["options"], "-fe=" + spec["link"], *spec["sources"]]]
    elif kind == "nasm":
        src = tree / spec["directory"]
        commands = [["nasm", *defines, *spec["command"]]]
    else:
        raise ValueError("unknown build kind: " + kind)
    for command in commands:
        subprocess.run(command, cwd=src, env=env, check=True,
                       stdout=subprocess.DEVNULL if command[0] == "wcl" else None)
    record = check_program(src / spec["link"])
    record["commands"] = [" ".join(c) for c in commands]
    record["platform_defines"] = defines
    record["working_directory"] = str(src.relative_to(output))
    shutil.copy2(src / spec["link"], output / spec["output"])
    return record


def build(components: Path, output: Path, names: list[str], revisions: dict[str, str],
          platform: bool = True) -> dict:
    output = output.resolve()
    if output.exists():
        raise FileExistsError("utility output directory must not already exist")
    watcom = Path(os.environ.get("WATCOM", ""))
    if not watcom.is_dir() or shutil.which("wcl") is None or shutil.which("nasm") is None:
        raise RuntimeError("the pinned Open Watcom installation, wcl and nasm are required")
    output.mkdir(parents=True)
    env = os.environ.copy()
    env["INCLUDE"] = str(watcom / "h")
    records = {}
    for name in names:
        record = build_one(name, components, output, env, platform)
        record.update(source_revisions=revisions[name], upx=False,
                      toolchain="Open Watcom 1.9 and NASM 2.15; identities are verified by the M20 toolchain lock",
                      messages="built-in English; kitten NLS catalogs are not installed")
        records[name] = record
        print("Built {}: {} bytes".format(TOOLS[name]["output"], record["file_size_bytes"]))
    (output / "utilities-build.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n",
                                                 encoding="ascii")
    return records


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--components", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-platform", action="store_true",
                        help="omit PC88VA defines (non-PC-88VA baseline build)")
    parser.add_argument("names", nargs="+")
    args = parser.parse_args()
    build(args.components, args.output, args.names, {n: {} for n in args.names},
          platform=not args.no_platform)


if __name__ == "__main__":
    main()
