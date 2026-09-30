#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build M18 twice from allowlisted Git exports and publish a local bundle."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

if __package__:
    from .normalize_parent_archive import records as parent_archive_records
    from .toolchain import verify_image
else:
    from normalize_parent_archive import records as parent_archive_records
    from toolchain import verify_image

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "build/m18"
DEFAULT_DIST = ROOT / "dist/m18"
PARENT_INPUTS = (
    "tools/m18", "tests/m18", "config/m18",
    "manifests/m18-components.lock.json", "manifests/toolchains.lock.json",
    "COPYING", "LICENSE.md",
)
COMPONENTS = ("fdkernel", "freecom", "country", "edlin", "jwasm")
DIST_MARKER = "M18-generated-distribution-root-v1\n"
BUILD_MARKER = "M18-generated-build-root-v1\n"


def run(*args: str, cwd: Path = ROOT, capture: bool = True) -> str:
    if capture:
        return subprocess.check_output(args, cwd=cwd, text=True).strip()
    subprocess.run(args, cwd=cwd, check=True)
    return ""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_hex(value: str, digits: int, name: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{%d}" % digits, value):
        raise ValueError("invalid {} identity".format(name))


def load_component_lock() -> tuple[dict, dict[str, dict]]:
    document = json.loads((ROOT / "manifests/m18-components.lock.json").read_text())
    if (document.get("milestone") != "M18" or
            document.get("start_sha") != "d81bba18f0e4793d7165fb0acfdf7e229e160c83"):
        raise ValueError("M18 source lock does not bind the selected start commit")
    entries = {item["name"]: item for item in document.get("components", [])}
    if set(entries) != set(COMPONENTS):
        raise ValueError("M18 component lock has an unexpected component set")
    return document, entries


def verify_parent_and_components() -> tuple[str, dict[str, str], dict]:
    parent = run("git", "rev-parse", "HEAD")
    verify_hex(parent, 40, "parent commit")
    lock, entries = load_component_lock()
    start = lock["start_sha"]
    run("git", "merge-base", "--is-ancestor", start, parent)
    integration = lock["parent_integration"]
    if (integration.get("merge_commit") != start or
            integration.get("first_parent") != "1af9974700cd4dd1164cc0df56cc062925376148" or
            integration.get("second_parent") != "06b0536feae627e9935277376b16630cb735fb24"):
        raise ValueError("M18 parent integration provenance differs from its lock")
    dirty = run("git", "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise ValueError("Commit all M18 parent build inputs before make m18-disk")
    sources = {"parent": parent}
    for name in COMPONENTS:
        item = entries[name]
        path = ROOT / "components" / name
        gitlink = run("git", "rev-parse", "HEAD:" + path.relative_to(ROOT).as_posix())
        child = run("git", "-C", str(path), "rev-parse", "HEAD")
        if child != gitlink or child != item["commit"]:
            raise ValueError("{} checkout/gitlink differs from the M18 source lock".format(name))
        if run("git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("{} source checkout is dirty".format(name))
        for remote, expected in (("origin", item["repository"]),
                                 ("upstream", item["upstream_repository"])):
            configured = subprocess.run(
                ["git", "-C", str(path), "config", "--get", "remote." + remote + ".url"],
                text=True, capture_output=True,
            )
            if configured.returncode:
                if remote != "upstream":
                    raise ValueError("{} origin remote is not configured".format(name))
                subprocess.run(["git", "-C", str(path), "remote", "add", remote, expected],
                               check=True)
                actual = expected
            else:
                actual = configured.stdout.strip()
            if actual.rstrip("/") != expected.rstrip("/"):
                raise ValueError("{} {} remote differs from public provenance".format(name, remote))
        verify_hex(item["source_archive_sha256"], 64, name + " source archive")
        sources[name] = child
    return parent, sources, lock


def image_identity(image: str) -> tuple[str, dict]:
    info = json.loads(run("docker", "image", "inspect", image))[0]
    if (info.get("Os"), info.get("Architecture")) != ("linux", "amd64"):
        raise ValueError("M18 requires the pinned Linux/amd64 toolchain image")
    lock = json.loads((ROOT / "manifests/toolchains.lock.json").read_text())["canonical"]
    if verify_image(image, lock) != info["Id"]:
        raise ValueError("M18 locally inspected toolchain identity changed")
    return info["Id"], info


def verify_output_root(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise ValueError(label + " root may not be a symlink")
    path = path.resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(label + " root must remain inside this repository") from exc
    ignored = subprocess.run(["git", "check-ignore", "-q", str(path / ".m18-probe")],
                             cwd=ROOT).returncode == 0
    if not ignored:
        raise ValueError(label + " root must be Git-excluded")
    return path


def safe_recreate(path: Path, marker: str, content: str, label: str) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise ValueError(label + " path exists but is not a regular generated directory")
        marker_path = path / marker
        if marker_path.is_symlink():
            raise ValueError("refusing to follow a generated-root marker symlink")
        if marker_path.is_file():
            if marker_path.read_text(encoding="ascii") != content:
                raise ValueError("refusing to remove mismatched {} directory".format(label))
            shutil.rmtree(path)
        elif any(path.iterdir()):
            raise ValueError("refusing to remove nonempty unmarked {} directory".format(label))
        else:
            path.rmdir()
    path.mkdir(parents=True)
    (path / marker).write_text(content, encoding="ascii")


def stage_distribution(path: Path) -> tuple[Path, bool]:
    if path.exists():
        if (path.is_symlink() or not path.is_dir() or
                (path / ".m18-generated-root").is_symlink() or
                not (path / ".m18-generated-root").is_file() or
                (path / ".m18-generated-root").read_text(encoding="ascii") != DIST_MARKER):
            raise ValueError("refusing to replace an unmarked M18 distribution directory")
        existing = True
    else:
        existing = False
    temporary = path.with_name(path.name + ".staging")
    if temporary.exists():
        marker_file = temporary / ".m18-generated-root"
        if (temporary.is_symlink() or not temporary.is_dir() or
                not marker_file.is_file() or
                marker_file.read_text(encoding="ascii") != DIST_MARKER):
            raise ValueError("refusing to remove an unmarked M18 staging directory")
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    (temporary / ".m18-generated-root").write_text(DIST_MARKER, encoding="ascii")
    return temporary, existing


def same_distribution(left: Path, right: Path) -> bool:
    def files(path):
        entries = list(path.rglob("*"))
        if any(item.is_symlink() for item in entries):
            raise ValueError("M18 distribution trees may not contain symlinks")
        return {item.relative_to(path).as_posix(): item.read_bytes()
                for item in entries if item.is_file() and
                item.name != ".m18-generated-root"}
    return files(left) == files(right)


def get_wheel(config: dict, inputs: Path) -> dict[str, str]:
    spec = config["unicorn_wheel"]
    fields = {"package", "version", "filename", "sha256", "python_tag",
              "abi_tag", "platform_tag"}
    if (set(spec) != fields or spec["package"] != "unicorn" or
            spec["version"] != "2.1.4" or
            spec["filename"] != "unicorn-2.1.4-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl" or
            spec["python_tag"] != "310" or spec["abi_tag"] != "cp310" or
            spec["platform_tag"] != "manylinux2014_x86_64"):
        raise ValueError("M18 Unicorn test-wheel pin is malformed")
    verify_hex(spec["sha256"], 64, "Unicorn wheel")
    cache_setting = os.environ.get("M18_WHEEL_CACHE")
    candidate = (Path(cache_setting).expanduser() / spec["filename"]
                 if cache_setting else None)
    target = inputs / spec["filename"]
    if candidate and candidate.is_file():
        shutil.copyfile(candidate, target)
    else:
        subprocess.run([
            sys.executable, "-m", "pip", "download", "--disable-pip-version-check",
            "--no-cache-dir", "--only-binary=:all:", "--no-deps",
            "--platform", spec["platform_tag"], "--python-version", spec["python_tag"],
            "--implementation", "cp", "--abi", spec["abi_tag"],
            "--dest", str(inputs), spec["package"] + "==" + spec["version"],
        ], check=True)
    data = target.read_bytes()
    if sha256(data) != spec["sha256"]:
        raise ValueError("M18 Unicorn wheel SHA-256 differs from its lock")
    if cache_setting and not (Path(cache_setting).expanduser() / spec["filename"]).exists():
        cache_dir = Path(cache_setting).expanduser()
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, cache_dir / spec["filename"])
    return {"package": spec["package"], "version": spec["version"],
            "filename": spec["filename"], "sha256": spec["sha256"]}


def create_exports(inputs: Path, parent: str, sources: dict[str, str], entries: dict[str, dict]) -> dict[str, str]:
    hashes = {}
    for name, revision in sources.items():
        archive = inputs / (name + ".tar")
        repo = ROOT if name == "parent" else ROOT / "components" / name
        command = ["git", "-C", str(repo), "archive", revision]
        if name == "parent":
            command.extend(PARENT_INPUTS)
        with archive.open("xb") as target:
            subprocess.run(command, cwd=ROOT, stdout=target, check=True)
        digest = sha256(archive.read_bytes())
        hashes[name] = digest
        if name != "parent" and digest != entries[name]["source_archive_sha256"]:
            raise ValueError("{} git archive SHA-256 differs from the source lock".format(name))
    return hashes


def normalize_parent_export_pinned(image_id: str, inputs: Path, epoch: int) -> str:
    """Bind a canonical Git-export TAR as both build input and source record.

    Only TAR metadata, never source contents or executable modes, is
    normalized. The canonicalizer runs with the locked container's Python.
    All five component archives remain untouched exact Git archives.
    """
    original = inputs / "parent.tar"
    canonical = inputs.parent / "canonical-parent.tar"
    command = (
        "mkdir -p /work/entry /work/result && "
        "tar -xf /input/parent.tar -C /work/entry "
        "tools/m18/normalize_parent_archive.py && "
        "python3 -B /work/entry/tools/m18/normalize_parent_archive.py "
        "/input/parent.tar /work/result/parent.tar "
        "--epoch \"$M18_SOURCE_DATE_EPOCH\""
    )
    cid = run("docker", "create", "--platform", "linux/amd64", "--network", "none",
              "-e", "M18_SOURCE_DATE_EPOCH=" + str(epoch), "--entrypoint", "bash",
              image_id, "-ec", command)
    try:
        subprocess.run(["docker", "cp", str(inputs) + "/.", cid + ":/input"], check=True)
        log = inputs.parent / "parent-normalization.log"
        with log.open("xb") as stream:
            subprocess.run(["docker", "start", "-a", cid], stdout=stream,
                           stderr=subprocess.STDOUT, check=True)
        subprocess.run(["docker", "cp", cid + ":/work/result/parent.tar",
                        str(canonical)], check=True)
    finally:
        subprocess.run(["docker", "rm", "-f", cid], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if parent_archive_records(original) != parent_archive_records(canonical):
        raise ValueError("parent Git export canonicalization changed source bytes or modes")
    canonical.replace(original)
    return sha256(original.read_bytes())


def tar_member(tar: tarfile.TarFile, name: str, data: bytes, epoch: int) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = epoch
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(data))


def build_source_bundle(inputs: Path, output: Path, source_record: dict, epoch: int) -> dict:
    package_readme = b"""PC-88VA FreeDOS M18 corresponding source bundle

This host-side bundle accompanies one native 2HD D88. It is not another DOS
disk. It contains the complete allowlisted M18 parent build inputs and the
full source archives of fdkernel, FreeCOM, COUNTRY.SYS, FreeDOS EDLIN, and JWasm.
Each source archive preserves its upstream license and notices. The root COPYING
is GPL version 2; JWasm's Sybase Open Watcom Public License 1.0 is included in
its source archive and as JWASM.LIC on the disk. The unmodified Open Watcom
1.9 DOS compiler runtime has independently pinned publicly obtainable source:
https://github.com/open-watcom/open-watcom-1.9/releases/download/ow1.9/open_watcom_1.9.0-src.tar.bz2
SHA-256: 6d303327988ee2dda60cfabebf3f45a9758aee4da117d41cf3153fccb7e5e4bf
It is a toolchain source release, not one of the five component archives in
this bundle. Its Sybase Open Watcom Public License 1.0 text matches JWASM.LIC
when normalized for line endings; the official *binary* compiler is pinned
separately by the project's toolchain lock.

For a reproducible image, use the exact parent commit and component gitlinks in
SOURCE-MANIFEST.json, initialize the pinned Linux/amd64 Open Watcom 1.9 image
with `python3 tools/m18/toolchain.py`, then run `make m18-disk`. Verify archive
hashes before using these sources. The package does not include private ROMs,
firmware, disk captures, guest traces, or emulator results.
"""
    manifest = {
        "schema_version": 1,
        "milestone": "M18",
        **source_record,
        "archive_members": ["parent.tar"] + [name + ".tar" for name in COMPONENTS],
    }
    temporary = output.with_suffix(".tmp")
    temporary.unlink(missing_ok=True)
    with tarfile.open(temporary, "w:xz", format=tarfile.PAX_FORMAT,
                      preset=9) as tar:
        base = "pc88va-freedos-m18-source/"
        tar_member(tar, base + "README.txt", package_readme, epoch)
        tar_member(tar, base + "SOURCE-MANIFEST.json",
                   (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("ascii"), epoch)
        for name in manifest["archive_members"]:
            data = (inputs / name).read_bytes()
            tar_member(tar, base + name, data, epoch)
    temporary.replace(output)
    with tarfile.open(output, "r:xz") as tar:
        names = tar.getnames()
        expected = {"pc88va-freedos-m18-source/README.txt",
                    "pc88va-freedos-m18-source/SOURCE-MANIFEST.json"}
        expected.update("pc88va-freedos-m18-source/" + name
                        for name in manifest["archive_members"])
        if set(names) != expected:
            raise ValueError("source bundle contains an unexpected member set")
    data = output.read_bytes()
    return {"filename": output.name, "size_bytes": len(data), "sha256": sha256(data)}


def build_source_bundle_pinned(image_id: str, inputs: Path, output: Path,
                               source_record: dict, epoch: int) -> dict:
    """Pack sources with the same pinned Python/liblzma as the DOS build.

    The host's Python and xz versions vary even when source archives and the
    normal D88 agree. Never let that change the designated companion archive.
    Copy only deterministic public exports into an isolated no-network
    container; do not mount a checkout or use cached DOS executables.
    """
    record = output.parent / "source-record.json"
    record.write_text(json.dumps(source_record, sort_keys=True) + "\n", encoding="ascii")
    script = (
        "mkdir -p /work/entry /work/result && "
        "tar -xf /input/parent.tar -C /work/entry "
        "tools/m18/build_image.py tools/m18/normalize_parent_archive.py "
        "tools/m18/toolchain.py && "
        "python3 -B -c 'import json,sys; from pathlib import Path; "
        "sys.path.insert(0,\"/work/entry/tools/m18\"); "
        "from build_image import build_source_bundle; "
        "build_source_bundle(Path(\"/input\"), "
        "Path(\"/work/result/freedos-PC88VA-M18-SOURCES.tar.xz\"), "
        "json.loads(Path(\"/work/source-record.json\").read_text()), "
        "int(sys.argv[1]))' \"$M18_SOURCE_DATE_EPOCH\""
    )
    cid = run("docker", "create", "--platform", "linux/amd64", "--network", "none",
              "-e", "M18_SOURCE_DATE_EPOCH=" + str(epoch), "--entrypoint", "bash",
              image_id, "-ec", script)
    try:
        subprocess.run(["docker", "cp", str(inputs) + "/.", cid + ":/input"], check=True)
        subprocess.run(["docker", "cp", str(record), cid + ":/work/source-record.json"],
                       check=True)
        log = output.parent / "source-bundle-build.log"
        with log.open("xb") as stream:
            subprocess.run(["docker", "start", "-a", cid], stdout=stream,
                           stderr=subprocess.STDOUT, check=True)
        subprocess.run(["docker", "cp", cid + ":/work/result/" + output.name,
                        str(output)], check=True)
    finally:
        subprocess.run(["docker", "rm", "-f", cid], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = output.read_bytes()
    with tarfile.open(output, "r:xz") as tar:
        if set(tar.getnames()) != {"pc88va-freedos-m18-source/README.txt",
                                   "pc88va-freedos-m18-source/SOURCE-MANIFEST.json"} | {
                                       "pc88va-freedos-m18-source/" + name + ".tar"
                                       for name in ("parent",) + COMPONENTS}:
            raise ValueError("pinned source bundle member set differs")
    return {"filename": output.name, "size_bytes": len(data), "sha256": sha256(data)}


def copy_container_run(image_id: str, toolchain_identity: str, inputs: Path, run_dir: Path,
                       parent: str, pass_number: int, source_date_epoch: int) -> dict:
    command = (
        "mkdir -p /work/entry && tar -xf /input/parent.tar -C /work/entry "
        "tools/m18/build_image.sh && bash /work/entry/tools/m18/build_image.sh"
    )
    cid = run("docker", "create", "--platform", "linux/amd64", "--network", "none",
              "-e", "M18_PARENT_SHA=" + parent,
              "-e", "M18_TOOLCHAIN_IDENTITY=" + toolchain_identity,
              "-e", "M18_SOURCE_DATE_EPOCH=" + str(source_date_epoch),
              "--entrypoint", "bash",
              image_id, "-ec", command)
    try:
        subprocess.run(["docker", "cp", str(inputs) + "/.", cid + ":/input"], check=True)
        log = run_dir.parent / ("build-{}.log".format(pass_number))
        with log.open("xb") as stream:
            try:
                subprocess.run(["docker", "start", "-a", cid], stdout=stream,
                               stderr=subprocess.STDOUT, check=True)
            except subprocess.CalledProcessError:
                failed = run_dir.parent / ("failed-{}".format(pass_number))
                subprocess.run(["docker", "cp", cid + ":/work/result", str(failed)],
                               check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                raise
        subprocess.run(["docker", "cp", cid + ":/work/result", str(run_dir)], check=True)
    finally:
        subprocess.run(["docker", "rm", "-f", cid], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    record = json.loads((run_dir / "artifacts.json").read_text(encoding="ascii"))
    if "media.d88" not in record:
        raise ValueError("M18 clean build omitted its D88")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    parser.add_argument("--image", default="freedos-pc88va-m18:local")
    args = parser.parse_args()

    output = verify_output_root(args.output, "M18 build")
    dist = verify_output_root(args.dist, "M18 distribution")
    parent, sources, lock = verify_parent_and_components()
    image_id, _ = image_identity(args.image)
    # Docker's local config ID varies with BuildKit metadata across hosts.
    # The committed lock pins the base, apt snapshot and compiler bytes; use
    # its stable digest in public records, not an unreproducible local image ID.
    toolchain_identity = "sha256:" + sha256(
        (ROOT / "manifests/toolchains.lock.json").read_bytes())
    safe_recreate(output, ".m18-generated-root", BUILD_MARKER, "M18 build")
    staging_dist, distribution_exists = stage_distribution(dist)
    inputs = output / "inputs"
    inputs.mkdir()
    source_archives = create_exports(inputs, parent, sources, {
        item["name"]: item for item in lock["components"]
    })
    host_config = json.loads((ROOT / "config/m18/host-tooling.json").read_text())
    epoch = host_config.get("source_date_epoch")
    if type(epoch) is not int or epoch <= 0:
        raise ValueError("M18 SOURCE_DATE_EPOCH is missing or invalid")
    source_archives["parent"] = normalize_parent_export_pinned(image_id, inputs, epoch)
    wheel = get_wheel(host_config, inputs)

    for number in (1, 2):
        run_dir = output / ("run-{}".format(number))
        copy_container_run(image_id, toolchain_identity, inputs, run_dir,
                           parent, number, epoch)
    first_d88 = (output / "run-1/media.d88").read_bytes()
    second_d88 = (output / "run-2/media.d88").read_bytes()
    if first_d88 != second_d88:
        raise ValueError("independent clean M18 builds produced different D88 bytes")
    for relative in ("package-manifest.json", "capacity-budget.json"):
        if (output / "run-1" / relative).read_bytes() != (output / "run-2" / relative).read_bytes():
            raise ValueError("independent M18 build release records differ: " + relative)
    run_one_artifacts = json.loads((output / "run-1/artifacts.json").read_text(encoding="ascii"))
    run_two_artifacts = json.loads((output / "run-2/artifacts.json").read_text(encoding="ascii"))
    expected_d88 = {"size_bytes": len(first_d88), "sha256": sha256(first_d88)}
    for record in (run_one_artifacts.get("media.d88"), run_two_artifacts.get("media.d88")):
        if record != expected_d88:
            raise ValueError("M18 artifact records do not bind the clean-built D88")
    comparison = {
        "schema_version": 1,
        "independent_clean_builds": 2,
        "media_d88_byte_identical": True,
        "media_d88_sha256": sha256(first_d88),
        "release_package_records_identical": True,
        "release_capacity_records_identical": True,
        "diagnostic_maps_are_not_part_of_the_distribution_reproducibility_claim": True,
    }
    (output / "two-build-comparison.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )

    source_record = {
        "parent_revision": parent,
        "parent_start_sha": lock["start_sha"],
        "components": {
            item["name"]: {
                "repository": item["repository"], "branch": item["branch"],
                "commit": item["commit"],
                "source_archive_sha256": item["source_archive_sha256"],
                "license": item["license"],
            } for item in lock["components"]
        },
        "source_archives_sha256": source_archives,
        "toolchain_identity": toolchain_identity,
        "host_test_wheel": wheel,
        "source_date_epoch": epoch,
        "two_independent_clean_builds_equal": True,
    }
    bundle_record = build_source_bundle_pinned(image_id, inputs,
        output / "freedos-PC88VA-M18-SOURCES.tar.xz", source_record, epoch)
    target_d88 = staging_dist / "freedos-PC88VA-M18-2HD.D88"
    target_d88.write_bytes(first_d88)
    shutil.copy2(output / "run-1/capacity-budget.json", staging_dist / "capacity-budget.json")
    shutil.copy2(output / "run-1/package-manifest.json", staging_dist / "package-manifest.json")
    shutil.copy2(output / "two-build-comparison.json", staging_dist / "two-build-comparison.json")
    shutil.copy2(output / "freedos-PC88VA-M18-SOURCES.tar.xz", staging_dist / "freedos-PC88VA-M18-SOURCES.tar.xz")
    readme = ROOT / "tools/m18/DISTRIBUTION-README.md"
    if not readme.is_file():
        raise FileNotFoundError("M18 distribution instructions are missing")
    shutil.copy2(readme, staging_dist / "README.md")
    final = {
        "schema_version": 1,
        "milestone": "M18",
        "parent_revision": parent,
        "parent_start_sha": lock["start_sha"],
        "component_revisions": sources,
        "source_archives_sha256": source_archives,
        "toolchain_identity": toolchain_identity,
        "host_test_wheel": wheel,
        "two_independent_clean_builds_equal": True,
        "two_build_comparison_sha256": sha256((staging_dist / "two-build-comparison.json").read_bytes()),
        "distribution_d88": {"filename": target_d88.name,
                             "size_bytes": len(first_d88),
                             "sha256": sha256(first_d88)},
        "source_bundle": bundle_record,
        "capacity_budget_sha256": sha256((staging_dist / "capacity-budget.json").read_bytes()),
        "package_manifest_sha256": sha256((staging_dist / "package-manifest.json").read_bytes()),
        "host_validation": "built/read back from public source inputs; guest qualification pending",
        "guest_boot": "NOT RUN BY make m18-disk",
        "hardware": "NOT RUN",
    }
    (staging_dist / "build-manifest.json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    if distribution_exists:
        if not same_distribution(dist, staging_dist):
            shutil.rmtree(staging_dist)
            raise ValueError("M18 output differs from the existing distribution; choose a new --dist path")
        shutil.rmtree(staging_dist)
    else:
        staging_dist.replace(dist)
    print("M18 D88: {} bytes SHA-256 {}".format(len(first_d88), sha256(first_d88)))
    print("M18 source bundle: {} bytes SHA-256 {}".format(
        bundle_record["size_bytes"], bundle_record["sha256"]))
    print("M18 public files: {}".format(dist))


if __name__ == "__main__":
    main()
