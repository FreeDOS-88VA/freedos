#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build JWASMR from the M18-pinned JWasm source with Open Watcom 1.9."""
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

SOURCE_MODULES = re.compile(r"\$\(OUTD\)/([A-Za-z0-9_]+)\.obj")
JWASM_DISABLED_FEATURES = (
    "COFF_SUPPORT", "ELF_SUPPORT", "AMD64_SUPPORT", "SSSE3SUPP",
    "SSE4SUPP", "OWFC_SUPPORT", "DLLIMPORT", "AVXSUPP", "PE_SUPPORT",
    "VMXSUPP", "SVMSUPP", "CVOSUPP", "COMDATSUPP", "STACKBASESUPP",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def verify_floating_runtime(map_text: str) -> None:
    # Pinned JWasm uses strtod() for REAL4/REAL8. The 16-bit OW runtime must
    # include its software 8087 emulator even when the user has no coprocessor.
    required = (
        "math87l.lib(strtod.c)", "emu87.lib(initemu.asm)",
        "emu87.lib(emu8087.asm)", "emu87.lib(dosinit.asm)",
    )
    if any(map_text.count(token) != 1 for token in required) or 'noemu87.lib(' in map_text:
        raise ValueError('JWASMR linked floating conversion lacks the pinned OW 1.9 DOS software 8087 runtime')


def parse_mz(executable: Path, map_file: Path) -> dict[str, object]:
    data = executable.read_bytes()
    if len(data) < 28:
        raise ValueError("JWASMR MZ header is truncated")
    (magic, last_page_bytes, page_count, relocation_count, header_paragraphs,
     minalloc, maxalloc, ss, sp, checksum, ip, cs, reloc_offset, overlay) = (
        struct.unpack_from("<14H", data)
    )
    if magic != 0x5A4D or page_count == 0 or last_page_bytes > 511:
        raise ValueError("JWASMR output is not a valid MZ executable")
    declared_size = ((page_count - 1) * 512 + last_page_bytes
                     if last_page_bytes else page_count * 512)
    header_size = header_paragraphs * 16
    if (declared_size != len(data) or header_size < 28 or
            header_size > declared_size or
            reloc_offset + relocation_count * 4 > header_size):
        raise ValueError("JWASMR MZ header and file extents disagree")
    image_bytes = declared_size - header_size
    image_paragraphs = (image_bytes + 15) // 16
    psp_block_paragraphs = 16 + image_paragraphs + minalloc
    stack_bytes = (ss * 16) + sp
    if psp_block_paragraphs > 0xFFFF or stack_bytes > (image_paragraphs + minalloc) * 16:
        raise ValueError("JWASMR MZ minimum allocation does not contain its stack")
    map_text = map_file.read_text(encoding="ascii", errors="strict")
    verify_floating_runtime(map_text)
    stack_match = re.search(
        r"^Stack size:\s+([0-9A-Fa-f]+)\s+\(([0-9]+)\.\)$",
        map_text, re.MULTILINE,
    )
    if not stack_match or int(stack_match.group(1), 16) != int(stack_match.group(2)):
        raise ValueError("JWASMR linker map has no consistent stack size")
    stack_size = int(stack_match.group(2))
    if stack_size != 0x8400:
        raise ValueError("JWASMR stack differs from the pinned upstream DOS16 recipe")
    if stack_bytes > (image_paragraphs + minalloc) * 16:
        raise ValueError("JWASMR initial stack lies outside its minimum allocation")
    return {
        "file_size_bytes": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "mz_header_bytes": header_size,
        "mz_image_bytes": image_bytes,
        "mz_image_paragraphs": image_paragraphs,
        "mz_minimum_extra_paragraphs": minalloc,
        "mz_maximum_extra_paragraphs": maxalloc,
        "required_psp_block_paragraphs": psp_block_paragraphs,
        "required_psp_block_bytes": psp_block_paragraphs * 16,
        "initial_stack_segment": ss,
        "initial_stack_pointer": sp,
        "initial_stack_end_from_psp_bytes": 16 * (ss + 16) + sp,
        "entry_cs": cs,
        "entry_ip": ip,
        "relocation_count": relocation_count,
        "relocation_table_offset": reloc_offset,
        "overlay_number": overlay,
        "linker_stack_bytes": stack_size,
        "cpu_target": "8086 (Open Watcom -0; JWasm OWDOS16 source recipe)",
        "floating_conversion_runtime": "OW 1.9 strtod plus linked DOS software 8087 emulator; real guest no-coprocessor conversion separately qualified",
    }


def build(source: Path, output: Path, source_revision: str) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    if not (source / "src/main.c").is_file() or not (source / "owmod.inc").is_file():
        raise ValueError("--source must be the pinned JWasm source tree")
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("JWASMR output must be separate from source and its parents")
    if output.exists():
        raise FileExistsError("JWASMR output directory must not already exist")
    output.mkdir(parents=True)
    objects = output / "objects"
    objects.mkdir()

    watcom = Path(os.environ.get("WATCOM", ""))
    if not watcom.is_dir():
        raise RuntimeError("WATCOM must name the pinned Open Watcom installation")
    tools = {}
    for name in ("wcc", "wlib", "wlink"):
        executable = shutil.which(os.environ.get(name.upper(), name))
        if executable is None:
            raise RuntimeError("Open Watcom {} is required".format(name))
        tools[name] = str(Path(executable).resolve())

    module_text = (source / "owmod.inc").read_text(encoding="ascii")
    modules = SOURCE_MODULES.findall(module_text)
    if len(modules) != len(set(modules)) or not modules:
        raise ValueError("JWasm OWDOS16 module list is empty or duplicated")
    sources = [source / "src/main.c"] + [source / "src/{}.c".format(m) for m in modules]
    missing = [str(path.relative_to(source)) for path in sources if not path.is_file()]
    if missing:
        raise ValueError("JWasm OWDOS16 source list is incomplete: {}".format(", ".join(missing)))

    env = os.environ.copy()
    env["LIB"] = str(watcom / "lib286") + ";" + str(watcom / "lib286/dos")
    flags = [
        "-q", "-0", "-w3", "-zc", "-ml", "-bc", "-bt=dos",
        "-Isrc/H", "-I" + str(watcom / "h"), "-obmilrs", "-s", "-DNDEBUG",
        "-DFASTMEM=0", "-DFASTPASS=0",
    ]
    flags.extend("-D{}=0".format(feature) for feature in JWASM_DISABLED_FEATURES)
    flags.append("-zt=12000")
    compiled = []
    for source_file in sources:
        object_file = objects / (source_file.stem + ".obj")
        run([tools["wcc"], *flags, "-fo=" + str(object_file),
             "src/{}.c".format(source_file.stem)], cwd=source, env=env)
        compiled.append(object_file)

    library = output / "JWASM.LIB"
    run([tools["wlib"], "-q", "-n", str(library),
         *["+" + str(obj) for obj in compiled[1:]]], cwd=output, env=env)

    executable = output / "JWASMR.EXE"
    map_file = output / "JWASMR.MAP"
    link_script = output / "jwasmr-link.lnk"
    link_script.write_text(
        "format dos\noption map={}\noption stack=0x8400\nfile {}\nlibrary {}\nname {}\n".format(
            map_file, compiled[0], library, executable
        ), encoding="ascii",
    )
    run([tools["wlink"], "@" + str(link_script)], cwd=output, env=env)
    record = parse_mz(executable, map_file)
    record.update({
        "source_revision": source_revision,
        "source_tree_sha256": {
            str(path.relative_to(source)): sha256(path)
            for path in [source / "OWDOS16.mak", source / "owmod.inc",
                         source / "src/H/msgdef.h"] + sources
        },
        "module_count": len(modules),
        "modules": modules,
        "toolchain": "Open Watcom 1.9; identities are verified by the M18 toolchain lock",
        "compiler_options": flags,
        "upstream_recipe": "OWDOS16.mak at the pinned JWasm source revision",
        "license_notice": "Banner names the Sybase OWP 1.0 license and M18 companion source path",
    })
    (output / "jwasmr-build.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    print("Built JWASMR.EXE: {} bytes; required PSP block {} paragraphs ({} bytes)".format(
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
