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
CURRENT_SOURCE = Path("manifests/current-components.json")
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
M17_STATUS = "M17 PASS (CONTRACTS/FIXTURES); HANDOFF READY"
M17_LOCK_FIELDS = {
    "components", "historical_components_lock", "m15_control", "milestone",
    "parent_integration", "predecessor", "predecessor_ci", "schema_version",
    "start_sha", "status",
}
M17_COMPONENT_FIELDS = {
    "country": {"branch", "commit", "name", "parent_commit", "path",
                "repository", "role", "source_archive_sha256"},
    "freecom": {"branch", "commit", "name", "parent_commit", "path",
                "repository", "role", "source_archive_sha256", "upstream"},
    "fdkernel": {"branch", "commit", "merge_parents", "name", "parent_commit",
                 "path", "repository", "role", "source_archive_sha256", "upstream"},
}


class CurrentComponentError(RuntimeError):
    """Raised when the selected current-component source is not exact."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise CurrentComponentError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _load_json(path: Path) -> tuple[bytes, dict]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CurrentComponentError(f"cannot parse component metadata: {exc}") from exc
    if not isinstance(value, dict):
        raise CurrentComponentError("component metadata must be a JSON object")
    return raw, value


def _load_canonical_json(path: Path) -> dict:
    raw, value = _load_json(path)
    canonical = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
    if raw != canonical:
        raise CurrentComponentError("current component lock is not canonical JSON")
    return value


def _normalize_m17_lock(lock: dict) -> dict:
    """Adapt the typed M17 provenance record to the legacy resolver shape."""
    if set(lock) != M17_LOCK_FIELDS:
        raise CurrentComponentError("M17 provenance lock has unknown or missing fields")
    if (type(lock.get("schema_version")) is not int or lock["schema_version"] != 2
            or lock.get("milestone") != "M17"
            or lock.get("start_sha") != "f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4"
            or lock.get("status") != M17_STATUS):
        raise CurrentComponentError("M17 provenance lock schema or acceptance status is invalid")
    if lock.get("historical_components_lock") != {
        "path": HISTORICAL_LOCK.as_posix(), "sha256": HISTORICAL_LOCK_SHA256
    }:
        raise CurrentComponentError("M17 provenance lock changed the historical lock binding")
    if lock.get("m15_control") != {
        "parent_commit": M15_CONTROL_COMMIT,
        "components": M15_CONTROL_COMPONENTS,
    }:
        raise CurrentComponentError("M17 provenance lock changed the M15 control")

    components = lock.get("components")
    if not isinstance(components, list) or len(components) != 3:
        raise CurrentComponentError("M17 provenance lock must contain exactly three components")
    by_name = {}
    for item in components:
        if not isinstance(item, dict) or item.get("name") not in M17_COMPONENT_FIELDS:
            raise CurrentComponentError("M17 provenance lock has an unknown component")
        name = item["name"]
        if name in by_name or set(item) != M17_COMPONENT_FIELDS[name]:
            raise CurrentComponentError(f"M17 component fields are invalid: {name}")
        expected_path = "components/" + name
        if item.get("path") != expected_path:
            raise CurrentComponentError(f"M17 component path is invalid: {name}")
        if not isinstance(item.get("commit"), str) or HEX40.fullmatch(item["commit"]) is None:
            raise CurrentComponentError(f"M17 component commit is invalid: {name}")
        parent = item.get("parent_commit")
        if parent is not None and (not isinstance(parent, str) or HEX40.fullmatch(parent) is None):
            raise CurrentComponentError(f"M17 component parent is invalid: {name}")
        if (not isinstance(item.get("source_archive_sha256"), str)
                or HEX64.fullmatch(item["source_archive_sha256"]) is None):
            raise CurrentComponentError(f"M17 source archive identity is invalid: {name}")
        by_name[name] = item
    if set(by_name) != set(M17_COMPONENT_FIELDS):
        raise CurrentComponentError("M17 provenance lock has an incomplete component set")

    policy = {
        "country": ("https://github.com/FDOS/country.git", "master"),
        "fdkernel": ("https://github.com/nakatamaho/fdkernel.git",
                     "topic/m17-storage-contracts-media-formats"),
        "freecom": ("https://github.com/nakatamaho/freecom_dbcs2.git",
                    "topic/m16-floppy-formats-console-input"),
    }
    for name, (repository, branch) in policy.items():
        if (by_name[name].get("repository"), by_name[name].get("branch")) != (repository, branch):
            raise CurrentComponentError(f"M17 component source policy is invalid: {name}")
    kernel = by_name["fdkernel"]
    merge_parents = [
        "1527da489528367bb8028a8e9576375d35722f50",
        "7883c8fac11fab20cb467ad0a93c8799f35b565a",
    ]
    if (kernel.get("parent_commit") != merge_parents[0]
            or kernel.get("merge_parents") != merge_parents):
        raise CurrentComponentError("M17 kernel merge provenance is invalid")

    return {
        "schema_version": 1,
        "status": "current-m17",
        "milestone": "M17",
        "historical_components_lock": lock["historical_components_lock"],
        "m15_control": lock["m15_control"],
        "components": components,
    }


def _select_current_lock(root: Path) -> tuple[Path, str | None]:
    selector_path = root / CURRENT_SOURCE
    if selector_path.is_symlink():
        raise CurrentComponentError("current-component selector must not be a symlink")
    if selector_path.exists():
        selector = _load_canonical_json(selector_path)
        expected_fields = {"kind", "milestone", "schema_version", "source"}
        if set(selector) != expected_fields or selector.get("kind") != "current-component-source":
            raise CurrentComponentError("current-component selector schema is invalid")
        source = selector.get("source")
        if (type(selector.get("schema_version")) is not int or selector["schema_version"] != 1
                or selector.get("milestone") != "M17"
                or not isinstance(source, dict)
                or set(source) != {"path", "schema_version", "sha256"}
                or source.get("path") != M17_LOCK.as_posix()
                or type(source.get("schema_version")) is not int
                or source["schema_version"] != 2
                or not isinstance(source.get("sha256"), str)
                or HEX64.fullmatch(source["sha256"]) is None):
            raise CurrentComponentError("current-component selector does not identify the M17 provenance schema")
        lock_path = root / M17_LOCK
        if lock_path.is_symlink() or not lock_path.is_file() or _sha256(lock_path) != source["sha256"]:
            raise CurrentComponentError("selected M17 provenance lock is missing or has digest drift")
        return M17_LOCK, "M17"
    if (root / M17_LOCK).exists():
        raise CurrentComponentError("M17 provenance lock requires an explicit current-component selector")
    if (root / M16_LOCK).exists():
        return M16_LOCK, "M16"
    if (root / M10_LOCK).exists():
        return M10_LOCK, "M10"
    if (root / M09_LOCK).exists():
        return M09_LOCK, "M09"
    if (root / M06_LOCK).exists():
        return M06_LOCK, "M06"
    return M06_LOCK, None


def resolve_current_components(root: Path, historical: dict[str, str]) -> dict[str, str]:
    """Return current gitlink expectations after validating the selected source."""
    root = root.resolve()
    if set(historical) != EXPECTED_PATHS:
        raise CurrentComponentError("historical component path set is invalid")
    selected_lock, milestone = _select_current_lock(root)
    if milestone is None and not (root / selected_lock).exists():
        return dict(historical)
    is_m09 = milestone == "M09"
    is_m10 = milestone == "M10"
    is_m16 = milestone in {"M16", "M17"}
    is_m17 = milestone == "M17"
    lock_path = root / selected_lock
    if _sha256(root / HISTORICAL_LOCK) != HISTORICAL_LOCK_SHA256:
        raise CurrentComponentError("historical component lock identity changed")
    if is_m17:
        _, provenance = _load_json(lock_path)
        data = _normalize_m17_lock(provenance)
    else:
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
    record_parent = expected_parent
    if is_m16:
        expected_parent = M15_CONTROL_COMPONENTS["components/fdkernel"]
        record_parent = expected_parent
    if is_m17:
        record_parent = "1527da489528367bb8028a8e9576375d35722f50"
        expected_merge_parents = [record_parent, "7883c8fac11fab20cb467ad0a93c8799f35b565a"]
        if fdkernel.get("merge_parents") != expected_merge_parents:
            raise CurrentComponentError("M17 fdkernel merge parents differ from the accepted integration")
    if (
        fdkernel.get("parent_commit") != record_parent
        or fdkernel.get("branch") != kernel_branch
        or not isinstance(archive, str)
        or HEX64.fullmatch(archive) is None
    ):
        raise CurrentComponentError("current fdkernel lineage or archive identity is invalid")
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
