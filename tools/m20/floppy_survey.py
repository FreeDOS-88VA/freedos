#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Survey FreeDOS 1.4 packages as candidates for a PC-88VA floppy set.

Host-only review aid; not a build input. It reads locally downloaded package
zips of the public FreeDOS 1.4 repository plus its listing.csv, and reports
for each package: version, group and license (listing.csv), LSM source/site
fields, whether source is included, source languages and build toolchains,
installed binary size, and heuristic indications of PC-hardware dependence
in the source (PC BIOS interrupts, BIOS data area, direct video memory, port
I/O). Heuristics only flag code for review; they do not decide viability.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

SOURCE_SUFFIXES = {".c": "C", ".h": "C", ".cpp": "C++", ".asm": "asm", ".inc": "asm",
                   ".mac": "asm", ".pas": "Pascal", ".s": "asm (gas)", ".bas": "BASIC"}
BINARY_SUFFIXES = (".exe", ".com", ".sys", ".bin", ".ovl")
TOOLS = {
    "Open Watcom": re.compile(rb"\b(wcl|wcc|wlink|wmake|owcc|wcl386)\b", re.I),
    "Turbo/Borland C": re.compile(rb"\b(tcc|bcc|tlink|tasm32|bc\.exe|turboc)\b", re.I),
    "Microsoft C/MASM": re.compile(rb"\b(cl\s|\bmasm\b|\bml\s|link\.exe|qcl)\b", re.I),
    "NASM": re.compile(rb"\bnasm\b", re.I),
    "TASM": re.compile(rb"\btasm\b", re.I),
    "JWasm/WASM": re.compile(rb"\b(jwasm|wasm)\b", re.I),
    "gcc-ia16": re.compile(rb"ia16-elf|\bgcc\b", re.I),
    "Pascal": re.compile(rb"\b(tpc|bpc|fpc|ppc8086)\b", re.I),
}
PC_HINTS = {
    "INT 10h video BIOS": re.compile(rb"int(86x?|r)?\s*\(\s*0x10\b|\bint\s+10h\b|geninterrupt\s*\(\s*0x10", re.I),
    "INT 13h disk BIOS": re.compile(rb"int(86x?|r)?\s*\(\s*0x13\b|\bint\s+13h\b|biosdisk|_bios_disk", re.I),
    "INT 15h system BIOS": re.compile(rb"int(86x?|r)?\s*\(\s*0x15\b|\bint\s+15h\b", re.I),
    "INT 16h keyboard BIOS": re.compile(rb"int(86x?|r)?\s*\(\s*0x16\b|\bint\s+16h\b|bioskey|_bios_keybrd", re.I),
    "INT 17h printer BIOS": re.compile(rb"int(86x?|r)?\s*\(\s*0x17\b|\bint\s+17h\b|biosprint", re.I),
    "INT 1Ah clock BIOS": re.compile(rb"int(86x?|r)?\s*\(\s*0x1a\b|\bint\s+1ah\b", re.I),
    "BIOS data area 0040h": re.compile(rb"MK_FP\s*\(\s*0x0*40\s*,|0x0*40\s*:\s*0x|\b0*40h\s*:|0x4[0-9a-f]{2}\b.*bios", re.I),
    "video memory B800/B000": re.compile(rb"0x?b[08]00\b|\bb[08]00h\b", re.I),
    "port I/O": re.compile(rb"\b(outp|inp|outportb?|inportb?|outpw|inpw)\s*\(|^\s*(out|in)\s+(dx|al|ax|[0-9])", re.I | re.M),
}


def lsm_fields(text: str) -> dict[str, str]:
    """Return fields of the English LSM entry (the one with a Version)."""
    entries = re.split(r"(?m)^End\s*$", text)
    for entry in entries:
        if re.search(r"(?m)^Version:", entry):
            fields, key = {}, None
            for line in entry.splitlines():
                m = re.match(r"([A-Za-z-]+):\s*(.*)", line)
                if m:
                    key = m.group(1); fields[key] = m.group(2).strip()
                elif key and line.startswith((" ", "\t")):
                    fields[key] += " " + line.strip()
            return fields
    return {}


def iter_members(archive: zipfile.ZipFile, depth: int = 0):
    """Yield (name, bytes) for members, descending into nested source zips."""
    for info in archive.infolist():
        if info.is_dir():
            continue
        data = archive.read(info)
        if info.filename.lower().endswith(".zip") and depth < 2:
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as nested:
                    for name, inner in iter_members(nested, depth + 1):
                        yield info.filename + "!" + name, inner
                continue
            except zipfile.BadZipFile:
                pass
        yield info.filename, data


def survey(package: str, path: Path, listing: dict) -> dict:
    record = {"package": package, "zip_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    meta = listing.get(package, {})
    for key in ("group", "version", "copying-policy", "modified-date", "description"):
        record[key] = meta.get(key, "")
    languages, tools, hints = {}, set(), {}
    binaries, has_source, lsm = 0, False, {}
    with zipfile.ZipFile(path) as archive:
        for name, data in iter_members(archive):
            lower = name.lower()
            top = lower.split("/", 1)[0]
            if top == "appinfo" and lower.endswith(".lsm"):
                lsm = lsm_fields(data.decode("latin-1")) or lsm
                continue
            in_source = top == "source" or "!" in lower
            if in_source:
                has_source = True
                suffix = Path(lower.split("!")[-1]).suffix
                if suffix in SOURCE_SUFFIXES:
                    lang = SOURCE_SUFFIXES[suffix]
                    languages[lang] = languages.get(lang, 0) + 1
                    for label, pattern in PC_HINTS.items():
                        count = len(pattern.findall(data))
                        if count:
                            hints[label] = hints.get(label, 0) + count
                base = Path(lower.split("!")[-1]).name
                if base.startswith(("makefile", "build")) or suffix in (".mak", ".bat", ".mk", ".sh", ".cfg", ".lnk"):
                    for label, pattern in TOOLS.items():
                        if pattern.search(data):
                            tools.add(label)
            elif top in ("bin", "devel", "driver", "drivers") or lower.endswith(BINARY_SUFFIXES):
                if lower.endswith(BINARY_SUFFIXES):
                    binaries += len(data)
    record.update({
        "lsm_version": lsm.get("Version", ""),
        "lsm_copying_policy": lsm.get("Copying-Policy", ""),
        "lsm_sites": " ".join(v for k, v in lsm.items() if k.endswith("Site") and "freedos/files" not in v),
        "lsm_platforms": lsm.get("Platforms", ""),
        "has_source": has_source,
        "languages": languages,
        "build_tools": sorted(tools),
        "binary_bytes": binaries,
        "pc_hints": hints,
    })
    return record


def markdown(records: list[dict]) -> str:
    out = ["| Package | Group | Version | License | Source | Languages | Build tools | Binaries (bytes) | PC-hardware hints |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in records:
        langs = ", ".join(f"{k} {v}" for k, v in sorted(r["languages"].items()))
        hints = ", ".join(f"{k} ({v})" for k, v in sorted(r["pc_hints"].items()))
        lic = (r["copying-policy"] or r["lsm_copying_policy"]).replace("|", "/")
        out.append(f"| {r['package']} | {r['group']} | {r['version']} | {lic} | "
                   f"{'yes' if r['has_source'] else 'no'} | {langs} | {', '.join(r['build_tools'])} | "
                   f"{r['binary_bytes']} | {hints} |")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path, required=True, help="one package name per line")
    parser.add_argument("--listing", type=Path, required=True, help="repository listing.csv")
    parser.add_argument("--zips", type=Path, required=True, help="directory of PACKAGE.zip files")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    listing = {row["package"]: row for row in
               csv.DictReader(io.StringIO(args.listing.read_bytes().decode("latin-1")))}
    names = [l.strip() for l in args.packages.read_text().splitlines() if l.strip()]
    records, absent = [], []
    for name in names:
        path = args.zips / (name + ".zip")
        if not path.exists():
            absent.append(name); continue
        records.append(survey(name, path, listing))
    if args.json:
        args.json.write_text(json.dumps({"records": records, "absent": absent}, indent=1) + "\n")
    if args.markdown:
        args.markdown.write_text(markdown(records))
    print(json.dumps({"surveyed": len(records), "absent": absent}))


if __name__ == "__main__":
    main()
