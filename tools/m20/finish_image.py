#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the M20 application set and compose one fresh native 2HD D88."""
from __future__ import annotations
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/m20"))
from build_compressed_kernel import build as build_carrier
from compose_image import compose
from media import derive_layout, inspect
from kernel_cc import banner_date, verify_banner


class PreText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_pre = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "pre":
            self.in_pre = True

    def handle_endtag(self, tag):
        if tag.lower() == "pre":
            self.in_pre = False

    def handle_data(self, data):
        if self.in_pre:
            self.parts.append(data)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_lock():
    document = json.loads((ROOT / "manifests/m20-components.lock.json").read_text())
    return {item["name"]: item for item in document["components"]}


def source_revision(name):
    return source_lock()[name]["commit"]


def read_text_payload(relative):
    data = (ROOT / relative).read_bytes()
    if any(byte >= 0x80 for byte in data):
        raise ValueError("non-ASCII disk text: " + relative)
    text = data.decode("ascii").replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n").encode("ascii")


def extract_jwasm_license():
    path = ROOT / "components/jwasm/Html/License.html"
    parser = PreText()
    parser.feed(path.read_text(encoding="ascii"))
    text = "".join(parser.parts).strip() + "\n"
    if not text or not text.isascii() or "Sybase Open Watcom Public License version 1.0" not in text:
        raise ValueError("JWasm on-disk license extraction failed closed")
    return text.encode("ascii")


def normalize_kernel_map(path):
    from datetime import datetime, timezone
    epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    stamp = datetime.fromtimestamp(epoch, timezone.utc).strftime("%y/%m/%d %H:%M:%S")
    text = path.read_text(encoding="ascii")
    text, count = re.subn(r"^Created on:.*$", "Created on:       " + stamp,
                          text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("kernel map lacks one reproducible Created on field")
    text, count = re.subn(r"^Link time:.*$", "Link time: 00:00.00",
                          text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("kernel map lacks one normalizable Link time field")
    path.write_text(text, encoding="ascii")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: finish_image.py OUTPUT_DIRECTORY")
    out = Path(sys.argv[1]).resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise ValueError("M20 image output must be an existing empty directory")
    profile = json.loads((ROOT / "config/m20/loader.json").read_text(encoding="ascii"))
    loader_dir = out / "loader"
    loader_dir.mkdir()
    from build_loader import build_stage
    stage2 = build_stage(profile, loader_dir, 2)
    shutil.copy2(loader_dir / "stage2.bin", out / "LOADER.BIN")
    (out / "stage2-manifest.json").write_text(
        json.dumps(stage2, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )

    kernel_tree = ROOT / "components/fdkernel/pc88va"
    kernel_linked = out / "kernel-linked.exe"
    kernel_map = out / "kernel.map"
    shutil.copy2(kernel_tree / "bin/KERNEL.SYS", kernel_linked)
    verify_banner(kernel_linked.read_bytes(), os.environ['SOURCE_DATE_EPOCH'])
    shutil.copy2(kernel_tree / "build/KVA8616.map", kernel_map)
    normalize_kernel_map(kernel_map)
    kernel_source = ROOT / "components/fdkernel/pc88va/kernel/m13_unpack.asm"
    config_source = ROOT / "config/m20/CONFIG.SYS"
    config_text = config_source.read_text(encoding="ascii")
    loadseg_match = re.search(r"^PC88VA_LOADSEG=([0-9A-Fa-f]+)h?\s*$",
                              config_text, flags=re.MULTILINE)
    if not loadseg_match:
        raise ValueError("M20 CONFIG.SYS has no explicit PC88VA_LOADSEG")
    pc88va_loadseg = int(loadseg_match.group(1), 16)
    kernel_file_low = profile["layout"]["regions"]["kernel_file"][0]
    scratch_low = profile["layout"]["regions"]["scratch"][0]
    ring_low = scratch_low + 0x1000
    if kernel_file_low & 15 or scratch_low & 15 or ring_low & 15:
        raise ValueError("M20 carrier segments are not paragraph aligned")
    carrier = build_carrier(
        kernel_linked, kernel_source, out / "KERNEL.SYS",
        load_segment=kernel_file_low // 16,
        file_segment=kernel_file_low // 16,
        scratch_segment=scratch_low // 16,
        source_offset=4096,
        image_segment=pc88va_loadseg,
        ring_offset=0,
        ring_segment=ring_low // 16,
        compact_bridge=True,
        link_map=kernel_map,
    )
    (out / "carrier.json").write_text(
        json.dumps(carrier, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    fdkernel_build = {
        "kernel_make_command": "wmake -ms -h -f makefile.m13.wc 'CC=python3 /work/source/tools/m20/kernel_cc.py' clean all",
        "banner_date_policy": {
            "source_date_epoch": int(os.environ['SOURCE_DATE_EPOCH']),
            "date": banner_date(os.environ['SOURCE_DATE_EPOCH']),
            "method": "compile-time KERNEL_BUILD_DATE definition; no linked-image patching",
        },
        "kernel_makefile_sha256": sha256((kernel_tree / "makefile.m13.wc").read_bytes()),
        "linked_kernel": {"size_bytes": kernel_linked.stat().st_size,
                          "sha256": sha256(kernel_linked.read_bytes())},
        "normalized_link_map": {"size_bytes": kernel_map.stat().st_size,
                                 "sha256": sha256(kernel_map.read_bytes()),
                                 "normalization": "Created on set from SOURCE_DATE_EPOCH; Link time set to 00:00.00"},
        "carrier": carrier,
        "stage2_loader": stage2,
        "pc88va_loadseg_paragraph": pc88va_loadseg,
        # The disk carries the CRLF-normalized payload, not the LF source file.
        "config_sys_sha256": sha256(read_text_payload("config/m20/CONFIG.SYS")),
        "config_sys_source_sha256": sha256(config_source.read_bytes()),
        "memory_qualification": "host layout verification only; guest RAM/MCB snapshots pending",
    }

    from edlin.build_edlin import build as build_edlin
    from assembler.build_jwasmr import build as build_jwasmr
    from memmap.build_memmap import build as build_memmap
    from programs.build_more import build as build_more
    from maintenance.build_maintenance import build as build_maintenance

    edlin_dir = out / "edlin"
    edlin = build_edlin(ROOT / "components/edlin", edlin_dir,
                        source_revision("edlin"))
    jwasm_dir = out / "jwasm"
    jwasmr = build_jwasmr(ROOT / "components/jwasm", jwasm_dir,
                          source_revision("jwasm"))
    memmap_dir = out / "memmap"
    memmap = build_memmap(memmap_dir)
    more_dir = out / "more"
    more = build_more(more_dir)
    maintenance_dir = out / "maintenance"
    maintenance = build_maintenance(maintenance_dir)

    source_epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    country_source = ROOT / "components/country/country.asm"
    import subprocess
    subprocess.run(["nasm", "-f", "bin", str(country_source), "-o",
                    str(out / "COUNTRY.SYS")], check=True)
    freecom = ROOT / "components/freecom/command.com"
    if not freecom.is_file():
        raise FileNotFoundError("isolated FreeCOM build did not produce command.com")
    shutil.copy2(freecom, out / "COMMAND.COM")
    timestamp_path = ROOT / "config/m20/freecom-build-timestamp.json"
    timestamp_config = json.loads(timestamp_path.read_text(encoding="ascii"))
    freecom_build = {
        "command": "bash build.sh pc88va no-xms-swap wc english; utils/ptchsize.exe command.com +3KB",
        "resident_heap_bytes": 3072,
        "build_script_sha256": sha256((ROOT / "components/freecom/build.sh").read_bytes()),
        "configuration_sha256": sha256((ROOT / "components/freecom/config.std").read_bytes()),
        "timestamp_config_sha256": sha256(timestamp_path.read_bytes()),
        "fixed_build_timestamp": timestamp_config,
    }
    country_build = {
        "command": "nasm -f bin components/country/country.asm -o COUNTRY.SYS",
        "assembler": "NASM from the pinned Linux/amd64 build environment",
        "source_sha256": sha256(country_source.read_bytes()),
    }

    shutil.copy2(edlin_dir / "EDLIN.EXE", out / "EDLIN.EXE")
    shutil.copy2(jwasm_dir / "JWASMR.EXE", out / "JWASMR.EXE")
    shutil.copy2(memmap_dir / "MEMMAP.EXE", out / "MEMMAP.EXE")
    shutil.copy2(more_dir / "MORE.EXE", out / "MORE.EXE")
    for name in ("CHKDSK", "FORMAT", "SYS"):
        shutil.copy2(maintenance_dir / (name + ".EXE"), out / (name + ".EXE"))

    # Stage 2 was assembled from the selected overlay above; the composer
    # derives its contiguous FAT extent and builds the matching stage 1.
    payloads = {name: (out / name).read_bytes() for name in (
        "LOADER.BIN", "KERNEL.SYS", "COMMAND.COM", "COUNTRY.SYS", "EDLIN.EXE",
        "MORE.EXE", "CHKDSK.EXE", "FORMAT.EXE", "SYS.EXE", "MEMMAP.EXE",
        "JWASMR.EXE",
    )}
    for name, relative in (
        ("CONFIG.SYS", "config/m20/CONFIG.SYS"),
        ("README.TXT", "config/m20/payload/README.TXT"),
        ("QUICKSTR.TXT", "config/m20/payload/QUICKSTR.TXT"),
        ("HELLO.ASM", "config/m20/payload/HELLO.ASM"),
        ("HELLO.DOC", "config/m20/payload/HELLO.DOC"),
        ("MZDEMO.ASM", "config/m20/payload/MZDEMO.ASM"),
        ("BUILD.BAT", "config/m20/payload/BUILD.BAT"),
    ):
        payloads[name] = read_text_payload(relative)
    payloads["COPYING"] = read_text_payload("COPYING")
    payloads["JWASM.LIC"] = extract_jwasm_license()

    compose(payloads, profile, out, source_epoch)
    d88 = (out / "media.d88").read_bytes()
    spec = json.loads((ROOT / "config/m20/media.json").read_text(encoding="ascii"))
    filesystem, files = inspect(d88, spec)
    if set(files) != set(payloads) or any(files[name] != payloads[name] for name in payloads):
        raise ValueError("independent native-media readback differs from release payloads")

    layout = derive_layout(spec)
    allocations = json.loads((out / "media.json").read_text(encoding="ascii"))["allocations"]
    package_config = json.loads((ROOT / "config/m20/packages.json").read_text(encoding="ascii"))
    from qa.tool_ram_budget import all_tool_floors
    dos_exec_floors = all_tool_floors(files)
    workspace = json.loads((ROOT / "config/m20/workspace-budget.json").read_text(encoding="ascii"))
    free_clusters = len(filesystem["free_clusters"])
    minimum_free = workspace["minimum_free_clusters_after_build"]
    if free_clusters < minimum_free:
        raise ValueError("native 2HD capacity fails M20 workspace reserve: {} < {} clusters".format(
            free_clusters, minimum_free))
    root_used = len(payloads) + 1  # The root volume-label entry owns one slot.
    if root_used > spec["filesystem"]["root_entries"]:
        raise ValueError("release payload exceeds the FAT12 root directory")

    file_records = {}
    for name, data in sorted(payloads.items()):
        row = allocations[name]
        inspected = filesystem["files"][name]
        if len(inspected["clusters"]) != row["sector_count"]:
            raise ValueError("host allocation record differs from independent media readback")
        file_records[name] = {
            "size_bytes": len(data),
            "sha256": sha256(data),
            "first_cluster": inspected["clusters"][0] if inspected["clusters"] else 0,
            "allocated_clusters": inspected["clusters"],
            "cluster_count": len(inspected["clusters"]),
            "allocation_slack_bytes": len(inspected["clusters"]) * 1024 - len(data),
        }
    capacity = {
        "schema_version": 1,
        "profile_id": "2hd-1280",
        "container": {"format": "D88", "size_bytes": len(d88), "sha256": sha256(d88)},
        "geometry": spec["geometry"],
        "filesystem": {
            "type": "FAT12",
            "logical_sector_bytes": 1024,
            "total_logical_sectors": 1280,
            "total_bytes": 1280 * 1024,
            "reserved_sectors": 1,
            "reserved_bytes": 1024,
            "fat_count": 2,
            "sectors_per_fat": 2,
            "fat_bytes": 4096,
            "fat12_bytes_required": layout["fat_bytes_required"],
            "root_entries": 192,
            "root_sectors": 6,
            "root_bytes": 6144,
            "root_entries_used": root_used,
            "root_entries_free": spec["filesystem"]["root_entries"] - root_used,
            "first_data_sector": layout["first_data_sector"],
            "data_cluster_bytes": 1024,
            "data_clusters_total": layout["data_clusters"],
            "data_clusters_allocated": layout["data_clusters"] - free_clusters,
            "data_clusters_free": free_clusters,
            "data_bytes_free": free_clusters * 1024,
            "file_payload_bytes": sum(map(len, payloads.values())),
            "file_records": file_records,
        },
        "workspace_budget": {
            "configured_free_clusters_floor": minimum_free,
            "configured_free_bytes_floor": workspace["minimum_free_bytes_after_build"],
            "sample_workflow_cluster_budget": workspace["sample_workflow"]["workspace_cluster_budget"],
            "sample_workflow_includes_edlin_backup": True,
            "guest_peak_measurement": "NOT MEASURED; owner removed instantaneous disk-workspace peak from M20 acceptance; this host reserve is not a guest measurement",
            "free_after_workflow_budget": free_clusters - workspace["sample_workflow"]["workspace_cluster_budget"],
        },
        "d88_and_fat_readback": "PASS; all payload bytes, FAT copies, geometry, and deterministic cluster chains were independently checked on host",
    }
    (out / "capacity-budget.json").write_text(
        json.dumps(capacity, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )

    parent_revision = os.environ.get("M20_PARENT_SHA", "")
    toolchain_identity = os.environ.get("M20_TOOLCHAIN_IDENTITY", "")
    if (not re.fullmatch(r"[0-9a-f]{40}", parent_revision) or
            not re.fullmatch(r"sha256:[0-9a-f]{64}", toolchain_identity)):
        raise ValueError("M20_PARENT_SHA and M20_TOOLCHAIN_IDENTITY must bind the build")
    source = source_lock()
    toolchain_lock_path = ROOT / "manifests/toolchains.lock.json"
    toolchain_lock_bytes = toolchain_lock_path.read_bytes()
    toolchain_lock = json.loads(toolchain_lock_bytes)
    package_manifest = {
        "schema_version": 1,
        "milestone": "M20",
        "parent_revision": parent_revision,
        "parent_start_sha": "ba868e2e33447fe5fcb3a2bed0711464f7968d82",
        "toolchain_identity": toolchain_identity,
        "toolchain_lock_sha256": sha256(toolchain_lock_bytes),
        "open_watcom_host_tools": toolchain_lock["canonical"]["open_watcom"]["host_tools"],
        "cpu_contract": package_config["cpu_contract"],
        "dos_executable_entry_lower_bounds": dos_exec_floors,
        "compiler_runtime_source": package_config["compiler_runtime_source"],
        "native_boot_profile": {
            "id": "2hd-1280",
            "geometry": spec["geometry"],
            "filesystem": spec["filesystem"],
        },
        "packages": [],
        "optional_tools": package_config["optional_tools"],
    }
    for item in package_config["packages"]:
        record = dict(item)
        files_for_package = record["files"]
        record["built_files"] = {
            filename: file_records[filename] for filename in files_for_package
            if filename in file_records
        }
        if record.get("source_lock"):
            source_item = source[record["source_lock"]]
            record["source_identity"] = {
                "repository": source_item["repository"],
                "branch": source_item["branch"],
                "commit": source_item["commit"],
                "source_archive_sha256": source_item["source_archive_sha256"],
            }
        else:
            record["source_identity"] = {
                "parent_revision": package_manifest["parent_revision"],
                "source_paths": ([record["source"]] if isinstance(record.get("source"), str)
                                 else record.get("source", [])),
            }
        record["build_records"] = {}
        if item["id"] == "fdkernel":
            record["build_records"] = fdkernel_build
        elif item["id"] == "freecom":
            record["build_records"] = freecom_build
        elif item["id"] == "country":
            record["build_records"] = country_build
        elif item["id"] == "edlin":
            record["build_records"] = edlin
        elif item["id"] == "jwasm":
            record["build_records"] = jwasmr
        elif item["id"] == "memmap":
            record["build_records"] = memmap
        elif item["id"] == "more":
            record["build_records"] = more
        elif item["id"] == "maintenance":
            record["build_records"] = maintenance
        package_manifest["packages"].append(record)
    (out / "package-manifest.json").write_text(
        json.dumps(package_manifest, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )

    artifacts = {
        path.relative_to(out).as_posix(): {
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path.read_bytes()),
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.name != "artifacts.json"
    }
    (out / "artifacts.json").write_text(
        json.dumps(artifacts, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    print("M20 native 2HD D88: {} bytes, SHA-256 {}".format(len(d88), sha256(d88)))
    print("M20 capacity: {} free clusters ({} bytes), reserve floor {} clusters".format(
        free_clusters, free_clusters * 1024, minimum_free))


if __name__ == "__main__":
    main()
