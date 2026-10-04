#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independently close the M20 public distribution's identity and file references.

No guest media or ROM is an input. Run after the complete two-build producer;
this is not an emulator acceptance claim.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

from media import inspect

ROOT = Path(__file__).resolve().parents[2]
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
BUILD_FIELDS = {
    "capacity_budget_sha256", "component_revisions", "distribution_d88",
    "guest_boot", "hardware", "host_test_wheel", "host_validation", "milestone",
    "package_manifest_sha256", "parent_revision", "parent_start_sha",
    "schema_version", "source_archives_sha256", "source_bundle",
    "toolchain_identity", "two_build_comparison_sha256", "two_independent_clean_builds_equal",
}
from data_disks import DATA_DISKS, comparison_fields, manifest_fields
BUILD_FIELDS |= manifest_fields()
from component_set import locked_names
COMPONENTS = set(locked_names(ROOT))


class VerificationError(ValueError):
    pass


def require(test: bool, message: str) -> None:
    if not test:
        raise VerificationError(message)


def fields(instance: dict, expected: set[str], name: str) -> None:
    require(isinstance(instance, dict) and set(instance) == expected,
            name + " has missing or unknown fields")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bound_file(directory: Path, name: str, expected_hash: str,
               expected_size: int | None = None) -> bytes:
    require(name == Path(name).name and name not in ("", ".", ".."),
            "unsafe distribution filename")
    require(isinstance(expected_hash, str) and HEX64.fullmatch(expected_hash) is not None,
            "malformed distribution hash for " + name)
    data = (directory / name).read_bytes()
    require(digest(data) == expected_hash and
            (expected_size is None or len(data) == expected_size),
            "distribution digest or size differs: " + name)
    return data


def check_manifest(manifest: dict, comparison: dict, budget: dict,
                   packages: dict, files: dict[str, bytes], bundle: bytes,
                   source_lock: dict, toolchain_lock_hash: str) -> None:
    """Check actual JSON instances, not just matching digests."""
    fields(manifest, BUILD_FIELDS, "build manifest")
    require(manifest["schema_version"] == 1 and manifest["milestone"] == "M20" and
            manifest["hardware"] == "NOT RUN" and
            manifest["guest_boot"] == "NOT RUN BY make m20-disk" and
            manifest["two_independent_clean_builds_equal"] is True,
            "build milestone/schema/two-build claim differs")
    parent = manifest["parent_revision"]
    require(isinstance(parent, str) and HEX40.fullmatch(parent) is not None and
            manifest["component_revisions"].get("parent") == parent and
            manifest["parent_start_sha"] == source_lock["start_sha"],
            "parent/source ancestry identity differs")
    revisions = manifest["component_revisions"]
    archives = manifest["source_archives_sha256"]
    require(set(revisions) == COMPONENTS | {"parent"} and set(archives) == set(revisions)
            and all(isinstance(v, str) and HEX40.fullmatch(v) for v in revisions.values())
            and all(isinstance(v, str) and HEX64.fullmatch(v) for v in archives.values()),
            "component/source archive topology or hash differs")
    locked = {item["name"]: item for item in source_lock["components"]}
    require(set(locked) == COMPONENTS and all(
        revisions[n] == locked[n]["commit"] and
        archives[n] == locked[n]["source_archive_sha256"] for n in COMPONENTS),
        "source lock/component provenance differs")
    require(manifest["toolchain_identity"] == packages["toolchain_identity"] ==
            "sha256:" + toolchain_lock_hash and
            packages["toolchain_lock_sha256"] == toolchain_lock_hash and
            packages["parent_revision"] == parent and
            packages["parent_start_sha"] == manifest["parent_start_sha"] and
            packages["milestone"] == "M20" and packages["schema_version"] == 1,
            "toolchain/package/parent references differ")
    fields(comparison, {"diagnostic_maps_are_not_part_of_the_distribution_reproducibility_claim",
                        "independent_clean_builds", "media_d88_byte_identical",
                        "media_d88_sha256", "release_capacity_records_identical",
                        "release_package_records_identical",
                        "schema_version"} | comparison_fields(),
           "two-build comparison")
    require(comparison["schema_version"] == 1 and comparison["independent_clean_builds"] == 2
            and comparison["media_d88_byte_identical"] is True
            and comparison["release_capacity_records_identical"] is True
            and comparison["release_package_records_identical"] is True
            and comparison["media_d88_sha256"] == manifest["distribution_d88"]["sha256"]
            and all(comparison[kind + "_d88_byte_identical"] is True
                    and comparison["release_" + kind + "_records_identical"] is True
                    and comparison[kind + "_d88_sha256"] == manifest[kind + "_d88"]["sha256"]
                    for kind in DATA_DISKS),
            "two-build instance disagrees with distribution")
    fields(budget, {"container", "d88_and_fat_readback", "filesystem", "geometry",
                    "profile_id", "schema_version", "workspace_budget"}, "capacity budget")
    require(budget["schema_version"] == 1 and
            budget["container"].get("sha256") == manifest["distribution_d88"]["sha256"],
            "budget image identity differs")
    require(budget["container"].get("size_bytes") == manifest["distribution_d88"]["size_bytes"]
            and budget["container"].get("format") == "D88"
            and budget["workspace_budget"].get("sample_workflow_cluster_budget") == 32
            and budget["workspace_budget"].get("configured_free_clusters_floor") == 128
            and "NOT MEASURED" in budget["workspace_budget"].get("guest_peak_measurement", ""),
            "capacity/reserve or unmeasured-peak policy differs")
    file_records = budget["filesystem"]["file_records"]
    require(set(file_records) == set(files) and
            all(record["sha256"] == digest(files[name]) and
                record["size_bytes"] == len(files[name])
                for name, record in file_records.items()),
            "capacity file reference missing, unknown or stale")
    expected_packages = {"fdkernel", "freecom", "country", "edlin", "more",
                         "maintenance", "memmap", "jwasm", "starter-material"}
    entries = packages["packages"]
    require(isinstance(entries, list) and len(entries) == len(expected_packages) and
            {item["id"] for item in entries} == expected_packages,
            "required package records missing, unknown or duplicate")
    declared = []
    for entry in entries:
        require(bool(entry["license"]) and set(entry["files"]) == set(entry["built_files"]),
                "package license or installed-file references missing")
        for name in entry["files"]:
            declared.append(name)
            record = entry["built_files"][name]
            require(name in files and record["sha256"] == digest(files[name]) and
                    record["size_bytes"] == len(files[name]),
                    "package file bytes differ: " + name)
    require(len(declared) == len(set(declared)) and set(files) == set(declared) | {"CONFIG.SYS"},
            "package-to-media file topology differs")
    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:xz") as archive:
        members = archive.getmembers()
        base = "pc88va-freedos-m20-source/"
        expected = {base + "README.txt", base + "SOURCE-MANIFEST.json"} | {
            base + name + ".tar" for name in revisions}
        require({m.name for m in members} == expected and
                len(members) == len(expected) and all(m.isfile() for m in members),
                "source bundle missing or unexpected archive member")
        source = json.load(archive.extractfile(base + "SOURCE-MANIFEST.json"))
        require(set(source["archive_members"]) == {name + ".tar" for name in revisions}
                and source["parent_revision"] == parent and
                source["toolchain_identity"] == manifest["toolchain_identity"] and
                source["source_archives_sha256"] == archives and
                all(source["components"][n]["commit"] == revisions[n] and
                    source["components"][n]["source_archive_sha256"] == archives[n]
                    for n in COMPONENTS), "source manifest references differ")
        for name, expected_hash in archives.items():
            require(digest(archive.extractfile(base + name + ".tar").read()) == expected_hash,
                    "source archive payload digest differs: " + name)


def check_utility(root: Path, distribution: Path, manifest: dict, source_lock: dict,
                  kind: str = "utility") -> None:
    """Check a data disk against its configuration and sources."""
    config = json.loads((root / DATA_DISKS[kind]["config"]).read_text())
    record = manifest[kind + "_d88"]
    fields(record, {"filename", "sha256", "size_bytes"}, kind + " D88 record")
    require(record["filename"] == config["disk"]["filename"], kind + " disk filename differs")
    image = bound_file(distribution, record["filename"], record["sha256"], record["size_bytes"])
    utility = json.loads(bound_file(distribution, kind + "-manifest.json",
                                    manifest[kind + "_manifest_sha256"]))
    fields(utility, {"disk", "files", "guest_qualification", "milestone", "notices", "packages",
                     "parent_revision", "schema_version", "toolchain_identity"}, kind + " manifest")
    require(utility["schema_version"] == 1 and utility["milestone"] == "M20" and
            utility["parent_revision"] == manifest["parent_revision"] and
            utility["toolchain_identity"] == manifest["toolchain_identity"] and
            utility["guest_qualification"] == "NOT RUN BY make m20-disk" and
            utility["disk"]["sha256"] == record["sha256"] and
            utility["disk"]["size_bytes"] == record["size_bytes"],
            kind + " manifest identity differs")
    spec = json.loads((root / "config/m20/media.json").read_text())
    spec["d88"]["disk_name"] = config["disk"]["d88_disk_name"]
    spec["image"]["volume_label"] = config["disk"]["volume_label"]
    readback, files = inspect(image, spec)
    require(readback["fat_copies_equal"], kind + " D88 FAT copies differ")
    require(set(files) == set(utility["files"]) and all(
        digest(files[n]) == utility["files"][n]["sha256"] and
        len(files[n]) == utility["files"][n]["size_bytes"] for n in files),
        kind + " disk files differ from their manifest")
    locked = {item["name"]: item for item in source_lock["components"]}
    declared = {"README.TXT"} | set(config["notices"])
    require(set(utility["notices"]) == set(config["notices"]), kind + " notices differ")
    require([p["id"] for p in utility["packages"]] == [p["id"] for p in config["packages"]],
            kind + " package records missing, unknown or reordered")
    for package, expected in zip(utility["packages"], config["packages"]):
        require(bool(package["license"]) and package["files"] == expected["files"] and
                set(package["built_files"]) == set(expected["files"]) and
                set(package["source_identity"]) == set(expected["source_locks"]),
                kind + " package record differs: " + package["id"])
        for name in expected["source_locks"]:
            identity = package["source_identity"][name]
            require(name in locked and identity["commit"] == locked[name]["commit"] and
                    identity["source_archive_sha256"] == locked[name]["source_archive_sha256"],
                    kind + " package source identity differs: " + package["id"])
        for name in expected["files"]:
            require(name in files and package["built_files"][name]["sha256"] == digest(files[name]),
                    kind + " package file bytes differ: " + name)
            declared.add(name)
    require(set(files) == declared, kind + " package-to-media file topology differs")


def verify(root: Path, distribution: Path) -> None:
    distribution = distribution.resolve()
    manifest = json.loads((distribution / "build-manifest.json").read_text())
    fields(manifest, BUILD_FIELDS, "build manifest")
    records = {}
    for key, filename in (("two_build_comparison_sha256", "two-build-comparison.json"),
                          ("capacity_budget_sha256", "capacity-budget.json"),
                          ("package_manifest_sha256", "package-manifest.json")):
        records[filename] = json.loads(bound_file(distribution, filename, manifest[key]))
    d88 = manifest["distribution_d88"]
    fields(d88, {"filename", "sha256", "size_bytes"}, "D88 record")
    require(d88["filename"] == "freedos-PC88VA-M20-2HD.D88", "normal disk filename differs")
    image = bound_file(distribution, d88["filename"], d88["sha256"], d88["size_bytes"])
    bundle_record = manifest["source_bundle"]
    fields(bundle_record, {"filename", "sha256", "size_bytes"}, "source bundle record")
    require(bundle_record["filename"] == "freedos-PC88VA-M20-SOURCES.tar.xz",
            "source bundle filename differs")
    bundle = bound_file(distribution, bundle_record["filename"],
                        bundle_record["sha256"], bundle_record["size_bytes"])
    spec = json.loads((root / "config/m20/media.json").read_text())
    readback, files = inspect(image, spec)
    require(readback["fat_copies_equal"] and
            records["capacity-budget.json"]["geometry"] == spec["geometry"],
            "normal D88 FATs or geometry/budget differ")
    check_manifest(manifest, records["two-build-comparison.json"],
                   records["capacity-budget.json"], records["package-manifest.json"],
                   files, bundle, json.loads((root / "manifests/m20-components.lock.json").read_text()),
                   digest((root / "manifests/toolchains.lock.json").read_bytes()))
    for kind in DATA_DISKS:
        check_utility(root, distribution, manifest,
                      json.loads((root / "manifests/m20-components.lock.json").read_text()), kind)
    print("M20 public acceptance instance: PASS (no emulator or hardware claim)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist/m20")
    args = parser.parse_args()
    verify(args.root.resolve(), args.dist)


if __name__ == "__main__":
    main()
