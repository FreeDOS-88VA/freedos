#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build pinned FreeDOS EDLIN for 8086 DOS with Open Watcom 1.9."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

SOURCE_FILES = ("edlin.c", "edlib.c", "defines.c", "dynstr.c",
                "config-h.ow", "msgs-en.h")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_mz(path: Path, map_path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 28:
        raise ValueError("EDLIN MZ header is truncated")
    (magic, last_page, pages, relocs, header_paras, minalloc, maxalloc,
     ss, sp, checksum, ip, cs, reloc_offset, overlay) = struct.unpack_from(
        "<14H", data
    )
    if magic != 0x5A4D or pages == 0 or last_page > 511:
        raise ValueError("EDLIN output is not a valid MZ executable")
    declared = (pages - 1) * 512 + last_page if last_page else pages * 512
    header_size = header_paras * 16
    if (declared != len(data) or header_size < 28 or header_size > declared or
            reloc_offset + relocs * 4 > header_size):
        raise ValueError("EDLIN MZ header and file extents disagree")
    image_bytes = declared - header_size
    image_paras = (image_bytes + 15) // 16
    required_paras = 16 + image_paras + minalloc
    stack_end_from_load_segment = 16 * ss + sp
    if (required_paras > 0xFFFF or
            stack_end_from_load_segment > (image_paras + minalloc) * 16):
        raise ValueError("EDLIN MZ minimum allocation does not contain its stack")
    text = map_path.read_text(encoding="ascii", errors="strict")
    stack = re.search(r"^Stack size:\s+([0-9A-Fa-f]+)\s+\(([0-9]+)\.\)$",
                      text, re.MULTILINE)
    if not stack or int(stack.group(1), 16) != int(stack.group(2)):
        raise ValueError("EDLIN linker map lacks a consistent stack size")
    stack_bytes = int(stack.group(2))
    if stack_bytes != 4096:
        raise ValueError("EDLIN stack differs from its recorded build setting")
    return {
        "file_size_bytes": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "mz_header_bytes": header_size,
        "mz_image_bytes": image_bytes,
        "mz_image_paragraphs": image_paras,
        "mz_minimum_extra_paragraphs": minalloc,
        "mz_maximum_extra_paragraphs": maxalloc,
        "required_psp_block_paragraphs": required_paras,
        "required_psp_block_bytes": required_paras * 16,
        "initial_stack_segment": ss,
        "initial_stack_pointer": sp,
        "initial_stack_end_from_psp_bytes": stack_end_from_load_segment + 256,
        "entry_cs": cs,
        "entry_ip": ip,
        "relocation_count": relocs,
        "relocation_table_offset": reloc_offset,
        "overlay_number": overlay,
        "stack_bytes": stack_bytes,
        "cpu_target": "8086 (Open Watcom -0)",
    }


def build(source: Path, output: Path, source_revision: str) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    if not (source / "edlin.c").is_file() or not (source / "COPYING").is_file():
        raise ValueError("--source must be the pinned FreeDOS EDLIN source tree")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("EDLIN output must be separate from source and its parents")
    if output.exists():
        raise FileExistsError("EDLIN output directory must not already exist")
    output.mkdir(parents=True)

    watcom = Path(os.environ.get("WATCOM", ""))
    if not watcom.is_dir():
        raise RuntimeError("WATCOM must name the pinned Open Watcom installation")
    compiler = shutil.which(os.environ.get("WCL", "wcl"))
    if compiler is None:
        raise RuntimeError("Open Watcom wcl is required")

    staged = output / "source"
    shutil.copytree(source, staged, ignore=shutil.ignore_patterns(".git"))
    for name in SOURCE_FILES:
        if not (staged / name).is_file():
            raise ValueError("EDLIN source package is missing {}".format(name))
    english = (staged / "msgs-en.h").read_bytes()
    if any(byte >= 0x80 for byte in english):
        raise ValueError("EDLIN English message source must be ASCII")
    config = (staged / "config-h.ow").read_bytes()
    (staged / "config.h").write_bytes(config)
    (staged / "msgs.h").write_bytes(english)

    env = os.environ.copy()
    env["WATCOM"] = str(watcom)
    env["INCLUDE"] = str(watcom / "h")
    executable = staged / "EDLIN.EXE"
    map_file = staged / "EDLIN.MAP"
    command = [
        compiler, "-q", "-bt=dos", "-ml", "-0", "-ox", "-k4096",
        "-dHAVE_CONFIG_H", "-i=" + str(staged), "-fm=" + str(map_file),
        "-fe=" + str(executable), "edlin.c", "edlib.c", "defines.c", "dynstr.c",
    ]
    subprocess.run(command, cwd=staged, env=env, check=True)
    record = parse_mz(executable, map_file)
    record.update({
        "source_revision": source_revision,
        "source_files": {
            name: sha256(staged / name) for name in SOURCE_FILES
        },
        "message_encoding": "ASCII",
        "shift_jis_build": False,
        "toolchain": "Open Watcom 1.9; identities are verified by the M18 toolchain lock",
        "compiler_options": ["-bt=dos", "-ml", "-0", "-ox", "-k4096",
                             "-dHAVE_CONFIG_H"],
        "license": "GPL-2.0-or-later; full COPYING is in the EDLIN source package and disk notices",
    })
    shutil.copy2(executable, output / "EDLIN.EXE")
    (output / "edlin-build.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    print("Built EDLIN.EXE: {} bytes; required PSP block {} paragraphs ({} bytes)".format(
        record["file_size_bytes"], record["required_psp_block_paragraphs"],
        record["required_psp_block_bytes"],
    ))
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    build(args.source, args.output, args.source_revision)


if __name__ == "__main__":
    main()
