#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build MEMMAP.EXE and bind its own-MCB shrink size to the linked MZ image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCES = (
    ROOT / "tools/m18/memmap/memmap.c",
    ROOT / "tools/m18/memmap/mcb_parser.c",
)


def run_wcl(output_dir, exe_name, map_name, paragraphs):
    compiler = shutil.which(os.environ.get("WCL", "wcl"))
    watcom = Path(os.environ.get("WATCOM", ""))
    if compiler is None or not watcom.is_dir():
        raise RuntimeError("Open Watcom wcl and its WATCOM installation are required")
    env = os.environ.copy()
    env["WATCOM"] = str(watcom)
    env["INCLUDE"] = str(watcom / "h")
    source_dir = ROOT / "tools/m18/memmap"
    command = [
        compiler, "-q", "-bt=dos", "-ml", "-0", "-k4096",
        "-dM18_REQUIRED_BLOCK_PARAGRAPHS=" + str(paragraphs),
        "-i=" + str(source_dir),
        "-fm=" + map_name,
        "-fe=" + exe_name,
        *(str(path) for path in SOURCES),
    ]
    subprocess.run(command, cwd=output_dir, env=env, check=True)


def parse_mz(path, map_path):
    data = Path(path).read_bytes()
    if len(data) < 28:
        raise ValueError("MEMMAP MZ header is truncated")
    (magic, last_page_bytes, page_count, relocations, header_paragraphs,
     min_allocation, max_allocation, stack_segment, stack_pointer, checksum,
     entry_ip, entry_cs, reloc_offset, overlay) = struct.unpack_from("<14H", data)
    if magic != 0x5a4d or page_count == 0 or last_page_bytes > 511:
        raise ValueError("MEMMAP output is not a valid DOS MZ executable")
    declared_file_size = (page_count - 1) * 512 + last_page_bytes if last_page_bytes else page_count * 512
    header_bytes = header_paragraphs * 16
    if (declared_file_size != len(data) or header_bytes < 28 or
            header_bytes > declared_file_size or reloc_offset + relocations * 4 > header_bytes):
        raise ValueError("MEMMAP MZ file/header extent is inconsistent")
    image_bytes = declared_file_size - header_bytes
    image_paragraphs = (image_bytes + 15) // 16
    required_paragraphs = 16 + image_paragraphs + min_allocation
    if required_paragraphs > 0xffff:
        raise ValueError("MEMMAP required PSP block exceeds the DOS paragraph limit")
    stack_end_bytes = (16 + stack_segment) * 16 + stack_pointer
    allocated_bytes = required_paragraphs * 16
    map_text = Path(map_path).read_text(encoding="ascii", errors="strict")
    stack_match = re.search(
        r"^Stack size:\s+([0-9A-Fa-f]+)\s+\(([0-9]+)\.\)$",
        map_text, re.MULTILINE,
    )
    memory_match = re.search(
        r"^Memory size:\s+([0-9A-Fa-f]+)\s+\(([0-9]+)\.\)$",
        map_text, re.MULTILINE,
    )
    if not stack_match or not memory_match:
        raise ValueError("MEMMAP linker map lacks stack or image-size evidence")
    stack_bytes = int(stack_match.group(2))
    map_memory_bytes = int(memory_match.group(2))
    if (int(stack_match.group(1), 16) != stack_bytes or
            int(memory_match.group(1), 16) != map_memory_bytes or
            stack_bytes != 4096 or min_allocation * 16 < stack_bytes):
        raise ValueError("MEMMAP stack/minalloc differs from its declared 4-KiB stack")
    if (stack_end_bytes > allocated_bytes or
            map_memory_bytes + 256 > allocated_bytes):
        raise ValueError("MEMMAP MZ minimum block does not cover linked image and stack")
    return {
        "file_size_bytes": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "mz_header_bytes": header_bytes,
        "mz_image_bytes": image_bytes,
        "mz_image_paragraphs": image_paragraphs,
        "mz_minimum_extra_paragraphs": min_allocation,
        "mz_maximum_extra_paragraphs": max_allocation,
        "required_psp_block_paragraphs": required_paragraphs,
        "required_psp_block_bytes": allocated_bytes,
        "linker_memory_size_bytes": map_memory_bytes,
        "bounded_stack_bytes": stack_bytes,
        "initial_stack_segment": stack_segment,
        "initial_stack_pointer": stack_pointer,
        "initial_stack_end_from_psp_bytes": stack_end_bytes,
        "entry_cs": entry_cs,
        "entry_ip": entry_ip,
        "relocation_count": relocations,
        "relocation_table_offset": reloc_offset,
        "overlay_number": overlay,
        "cpu_target": "8086",
        "compiler_options": ["-bt=dos", "-ml", "-0", "-k4096"],
    }


def build(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    probe = output / "probe"
    final = output / "final"
    probe.mkdir(exist_ok=False)
    final.mkdir(exist_ok=False)

    run_wcl(probe, "MEMMAP-PROBE.EXE", "MEMMAP-PROBE.MAP", 0)
    probe_record = parse_mz(probe / "MEMMAP-PROBE.EXE",
                            probe / "MEMMAP-PROBE.MAP")
    required = probe_record["required_psp_block_paragraphs"]

    run_wcl(final, "MEMMAP.EXE", "MEMMAP.MAP", required)
    final_record = parse_mz(final / "MEMMAP.EXE", final / "MEMMAP.MAP")
    if final_record["required_psp_block_paragraphs"] != required:
        raise ValueError("MEMMAP self-sizing changed between linked passes")
    source_files = SOURCES + (ROOT / "tools/m18/memmap/mcb_parser.h",)
    final_record["source_sha256"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files
    }
    final_record["probe_mz_sha256"] = probe_record["file_sha256"]
    final_record["shrink_method"] = (
        "INT 21h/AH=4Ah to PSP size derived from MZ header image paragraphs, "
        "minimum extra allocation, and the 256-byte PSP"
    )
    (final / "memmap-build.json").write_text(
        json.dumps(final_record, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    shutil.copy2(final / "MEMMAP.EXE", output / "MEMMAP.EXE")
    shutil.copy2(final / "memmap-build.json", output / "memmap-build.json")
    print("Built MEMMAP.EXE; required process block: {} paragraphs ({} bytes)".format(
        required, required * 16
    ))
    return final_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
