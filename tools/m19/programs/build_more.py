#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the DOS-service MORE pager as a bounded 8086 MZ executable."""
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

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/m19/programs/more.c"


def parse_mz(executable: Path, map_file: Path) -> dict[str, object]:
    data = executable.read_bytes()
    if len(data) < 28:
        raise ValueError("MORE MZ header is truncated")
    (magic, last, pages, relocations, header_paras, minalloc, maxalloc,
     ss, sp, checksum, ip, cs, reloc_offset, overlay) = struct.unpack_from(
        "<14H", data
    )
    declared = (pages - 1) * 512 + last if last else pages * 512
    header_bytes = header_paras * 16
    if (magic != 0x5a4d or not pages or last > 511 or declared != len(data) or
            header_bytes < 28 or header_bytes > declared or
            reloc_offset + relocations * 4 > header_bytes):
        raise ValueError("MORE MZ header/file extents are inconsistent")
    image_bytes = declared - header_bytes
    image_paras = (image_bytes + 15) // 16
    required = 16 + image_paras + minalloc
    stack_end = 16 * ss + sp
    if required > 0xffff or stack_end > (image_paras + minalloc) * 16:
        raise ValueError("MORE minimum DOS allocation does not contain its stack")
    text = map_file.read_text(encoding="ascii")
    stack = re.search(r"^Stack size:\s+([0-9A-Fa-f]+)\s+\(([0-9]+)\.\)$",
                      text, re.MULTILINE)
    memory = re.search(r"^Memory size:\s+([0-9A-Fa-f]+)\s+\(([0-9]+)\.\)$",
                       text, re.MULTILINE)
    if not stack or not memory:
        raise ValueError("MORE linker map lacks stack/image-size evidence")
    stack_bytes, memory_bytes = int(stack.group(2)), int(memory.group(2))
    if (int(stack.group(1), 16) != stack_bytes or
            int(memory.group(1), 16) != memory_bytes or stack_bytes != 2048 or
            minalloc * 16 < stack_bytes or memory_bytes + 256 > required * 16 or
            stack_end > required * 16):
        raise ValueError("MORE linked MZ allocation differs from the 2-KiB stack contract")
    return {
        "file_size_bytes": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "mz_header_bytes": header_bytes,
        "mz_image_bytes": image_bytes,
        "mz_image_paragraphs": image_paras,
        "mz_minimum_extra_paragraphs": minalloc,
        "mz_maximum_extra_paragraphs": maxalloc,
        "required_psp_block_paragraphs": required,
        "required_psp_block_bytes": required * 16,
        "linked_memory_size_bytes": memory_bytes,
        "stack_bytes": stack_bytes,
        "initial_stack_segment": ss,
        "initial_stack_pointer": sp,
        "entry_cs": cs,
        "entry_ip": ip,
        "relocation_count": relocations,
        "relocation_table_offset": reloc_offset,
        "overlay_number": overlay,
        "cpu_target": "8086 (Open Watcom -0)",
        "compiler_options": ["-bt=dos", "-ml", "-0", "-ox", "-k2048"],
    }


def build(output: Path) -> dict[str, object]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError("MORE output directory must not already exist")
    output.mkdir(parents=True)
    compiler = shutil.which(os.environ.get("WCL", "wcl"))
    watcom = Path(os.environ.get("WATCOM", ""))
    if not compiler or not watcom.is_dir():
        raise RuntimeError("Pinned Open Watcom wcl and WATCOM are required")
    exe, map_file = output / "MORE.EXE", output / "MORE.MAP"
    command = [compiler, "-q", "-bt=dos", "-ml", "-0", "-ox", "-k2048",
               "-fm=" + str(map_file), "-fe=" + str(exe), str(SOURCE)]
    subprocess.run(command, cwd=output, check=True)
    record = parse_mz(exe, map_file)
    record["source_sha256"] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    record["dos_services"] = ["DOS file I/O through Open Watcom C runtime",
                              "INT 21h/AH=06h nonblocking console input",
                              "INT 21h/AX=4400h/4401h: redirected stdin keeps the data; keys come from a raw CON handle",
                              "DOS stdout/stderr; no IBM BIOS calls"]
    record["license"] = "GPL-2.0-or-later"
    (output / "more-build.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    print("Built MORE.EXE: {} bytes; required DOS block {} paragraphs ({} bytes)".format(
        record["file_size_bytes"], record["required_psp_block_paragraphs"],
        record["required_psp_block_bytes"]))
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)


if __name__ == "__main__":
    main()
