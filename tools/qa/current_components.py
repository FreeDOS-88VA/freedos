#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Resolve the current component identity without rewriting historical locks."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


M06_LOCK = Path("manifests/m08-components.lock.json")
M09_LOCK = Path("manifests/m09-components.lock.json")
M10_LOCK = Path("manifests/m10-components.lock.json")
M17_LOCK = Path("manifests/m17-components.lock.json")
M16_LOCK = Path("manifests/m16-components.lock.json")
HISTORICAL_LOCK = Path("manifests/components.lock.json")
HISTORICAL_LOCK_SHA256 = "440e481b28c740875489a6953a246ce5370c44074053c7aad3f80e79ec40c19c"
M15_CONTROL_COMMIT = "1af9974700cd4dd1164cc0df56cc062925376148"
M15_CONTROL_COMPONENTS = {
    "components/country": "23f189cca3420606eae8723884fa92ccd65eb307",
    "components/fdkernel": "d8dbbf7111f86ea4800daeac84ac53ba601aaf32",
    "components/freecom": "9cf57b28abf1d98fab7655fb811375a2aa16c6d9",
}
EXPECTED_PATHS = {
    "components/country",
    "components/fdkernel",
    "components/freecom",
}
EXPECTED_POLICY = {
    "components/country": ("country", "https://github.com/FDOS/country.git", "master"),
    "components/fdkernel": ("fdkernel", "https://github.com/nakatamaho/fdkernel.git", "necpc88va"),
    "components/freecom": ("freecom", "https://github.com/nakatamaho/freecom_dbcs2.git", "deterministic-build-timestamp"),
}
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")


class CurrentComponentError(RuntimeError):
    """Raised when the M06 current-component overlay is not exact."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_canonical_json(path: Path) -> dict:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CurrentComponentError(f"cannot parse current component lock: {exc}") from exc
    canonical = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
    if raw != canonical:
        raise CurrentComponentError("current component lock is not canonical JSON")
    return value


def resolve_current_components(root: Path, historical: dict[str, str]) -> dict[str, str]:
    """Return current gitlink expectations after validating the M06 overlay."""
    root = root.resolve()
    if set(historical) != EXPECTED_PATHS:
        raise CurrentComponentError("historical component path set is invalid")
    is_m09 = (root / M09_LOCK).exists()
    is_m10 = (root / M10_LOCK).exists()
    is_m17 = (root / M17_LOCK).exists()
    is_m16 = (root / M16_LOCK).exists() or is_m17
    lock_path = root / (M17_LOCK if is_m17 else M16_LOCK if is_m16 else M10_LOCK if is_m10 else M09_LOCK if is_m09 else M06_LOCK)
    if not lock_path.exists():
        return dict(historical)
    if _sha256(root / HISTORICAL_LOCK) != HISTORICAL_LOCK_SHA256:
        raise CurrentComponentError("historical component lock identity changed")
    data = _load_canonical_json(lock_path)
    if is_m09 and _sha256(root / M06_LOCK) != "c3e736596ce63ce006ba0363682259260f30a1792e59a04e3250ac9821544f07":
        raise CurrentComponentError("M09 changed its accepted M08 predecessor lock")
    if is_m10 and _sha256(root / M09_LOCK) != "9f6fc653d22655ff797d722237994f1251b93306d3fbc4f0a145baaec565fa58":
        raise CurrentComponentError("M10 changed its accepted M09 predecessor lock")
    expected_status = "current-m09" if is_m09 else "current-m08"
    kernel_branch = "topic/m09-pc88va-early-console-output" if is_m09 else "topic/m08-pc88va-disk-loader-handoff"
    if is_m10:
        expected_status = "current-m10"
        kernel_branch = "topic/m10-pc88va-machine-services-init"
    if is_m16:
        expected_status = "current-m16"
        kernel_branch = "topic/m16-floppy-formats-console-input"
    if is_m17:
        expected_status = "current-m17"
        kernel_branch = "topic/m17-storage-contracts-media-formats"
    if (
        data.get("schema_version") != 1
        or data.get("status") != expected_status
        or (is_m16 and data.get("milestone") != ("M17" if is_m17 else "M16"))
    ):
        raise CurrentComponentError("current component lock schema or status is invalid")
    historical_record = data.get("historical_components_lock")
    if historical_record != {"path": HISTORICAL_LOCK.as_posix(), "sha256": HISTORICAL_LOCK_SHA256}:
        raise CurrentComponentError("current lock does not preserve the historical lock identity")
    components = data.get("components")
    if not isinstance(components, list) or len(components) != 3:
        raise CurrentComponentError("current component lock must contain exactly three components")
    by_path = {}
    for item in components:
        if not isinstance(item, dict) or item.get("path") in by_path:
            raise CurrentComponentError("current component lock contains an invalid or duplicate entry")
        by_path[item.get("path")] = item
    if set(by_path) != EXPECTED_PATHS:
        raise CurrentComponentError("current component lock path set is invalid")
    current = {}
    for path in sorted(EXPECTED_PATHS):
        expected_name, expected_repository, expected_branch = EXPECTED_POLICY[path]
        if path == "components/fdkernel":
            expected_branch = kernel_branch
        if is_m16 and path == "components/freecom":
            expected_branch = "topic/m16-floppy-formats-console-input"
        if (
            by_path[path].get("name") != expected_name
            or by_path[path].get("repository") != expected_repository
            or by_path[path].get("branch") != expected_branch
        ):
            raise CurrentComponentError(f"current component provenance policy is invalid: {path}")
        commit = by_path[path].get("commit")
        if not isinstance(commit, str) or HEX40.fullmatch(commit) is None:
            raise CurrentComponentError(f"current component commit is invalid: {path}")
        current[path] = commit
    if is_m16:
        control = data.get("m15_control")
        if control != {
            "parent_commit": M15_CONTROL_COMMIT,
            "components": M15_CONTROL_COMPONENTS,
        }:
            raise CurrentComponentError("M16 does not preserve the exact M15 control")
        for path, expected_commit in M15_CONTROL_COMPONENTS.items():
            try:
                pinned = subprocess.run(
                    ("git", "rev-parse", f"{M15_CONTROL_COMMIT}:{path}"),
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
            except subprocess.CalledProcessError as exc:
                raise CurrentComponentError("M15 control commit is unavailable") from exc
            if pinned != expected_commit:
                raise CurrentComponentError(f"M15 control component pin differs: {path}")
        freecom = "components/freecom"
        freecom_parent = M15_CONTROL_COMPONENTS[freecom]
        if (
            current[freecom] == freecom_parent
            or by_path[freecom].get("parent_commit") != freecom_parent
        ):
            raise CurrentComponentError("M16 FreeCOM must descend from the exact M15 control")
        result = subprocess.run(
            ("git", "merge-base", "--is-ancestor", freecom_parent, current[freecom]),
            cwd=root / freecom,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode:
            raise CurrentComponentError("M16 FreeCOM commit is not a descendant of the M15 control")
        path = "components/country"
        if current[path] != M15_CONTROL_COMPONENTS[path] or by_path[path].get("parent_commit") is not None:
            raise CurrentComponentError(f"M16 unexpectedly changes {path}")
    else:
        for path in ("components/freecom", "components/country"):
            if current[path] != historical[path] or by_path[path].get("parent_commit") is not None:
                raise CurrentComponentError(f"M06 unexpectedly changes {path}")
    fdkernel = by_path["components/fdkernel"]
    archive = fdkernel.get("source_archive_sha256")
    expected_parent = historical["components/fdkernel"] if data.get("status") == "current-m06" else "69ccdd8699895722fc537d647ec490685532bdc4"
    if is_m09:
        expected_parent = "105d49a72ec41afe07fc1e7b080bdbd1b3026ae2"
    if is_m10:
        expected_parent = "ef46a7ad4b381cf7a301899bee00fec99f5e37a7"
    if is_m16:
        expected_parent = M15_CONTROL_COMPONENTS["components/fdkernel"]
    if (
        fdkernel.get("parent_commit") != expected_parent
        or fdkernel.get("branch") != kernel_branch
        or not isinstance(archive, str)
        or HEX64.fullmatch(archive) is None
    ):
        raise CurrentComponentError("M06 fdkernel lineage or archive identity is invalid")
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", expected_parent, current["components/fdkernel"]),
        cwd=root / "components/fdkernel",
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode:
        raise CurrentComponentError("M06 fdkernel commit is not a descendant of the historical commit")
    if is_m16:
        for path, item in by_path.items():
            archive = item.get("source_archive_sha256")
            if not isinstance(archive, str) or HEX64.fullmatch(archive) is None:
                raise CurrentComponentError(f"M16 source archive identity is invalid: {path}")
            archived = subprocess.run(
                ("git", "archive", current[path]),
                cwd=root / path,
                check=True,
                capture_output=True,
            ).stdout
            if hashlib.sha256(archived).hexdigest() != archive:
                raise CurrentComponentError(f"M16 source archive digest differs: {path}")
    return current
