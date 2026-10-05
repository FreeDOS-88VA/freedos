#!/usr/bin/env python3
"""Verify the public M00 scaffold without network access or file changes."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "qa"))
from current_components import CurrentComponentError, resolve_current_components


EXPECTED_SUBMODULES = {
    "components/fdkernel": {
        "name": "fdkernel",
        "url": "https://github.com/FreeDOS-88VA/fdkernel.git",
        # The scaffold lock is a hash-pinned historical record (pre-transfer URL).
        "lock_url": "https://github.com/nakatamaho/fdkernel.git",
        "branch": "nec98-current",
    },
    "components/freecom": {
        "name": "freecom",
        "url": "https://github.com/FreeDOS-88VA/freecom_dbcs2.git",
        # The scaffold lock is a hash-pinned historical record (pre-transfer URL).
        "lock_url": "https://github.com/nakatamaho/freecom_dbcs2.git",
        "branch": "deterministic-build-timestamp",
    },
    "components/country": {
        "name": "country",
        "url": "https://github.com/FDOS/country.git",
        "branch": "master",
    },
}

REQUIRED_FILES = {
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/pull_request_template.md",
    ".github/workflows/scaffold.yml",
    "components/README.md",
    "config/README.md",
    "config/local.env.example",
    "config/stage0/.gitkeep",
    "config/japanese/.gitkeep",
    "docs/README.md",
    "docs/architecture/repository-layout.md",
    "docs/build/README.md",
    "docs/compatibility/README.md",
    "docs/decisions/README.md",
    "docs/decisions/0000-record-template.md",
    "docs/hardware/README.md",
    "docs/licensing/README.md",
    "docs/milestones/README.md",
    "docs/milestones/M00-scaffold.md",
    "docs/provenance/components.md",
    "docs/qa/test-matrix.md",
    "images/README.md",
    "images/layouts/README.md",
    "images/output/.gitkeep",
    "manifests/README.md",
    "manifests/components.lock.json",
    "manifests/packages.lock.yml",
    "manifests/licenses.yml",
    "mk/host.mk",
    "mk/components.mk",
    "mk/image.mk",
    "mk/qa.mk",
    "overlays/README.md",
    "overlays/stage0/.gitkeep",
    "overlays/japanese/.gitkeep",
    "patches/README.md",
    "patches/fdkernel/.gitkeep",
    "patches/freecom/.gitkeep",
    "patches/country/.gitkeep",
    "patches/packages/.gitkeep",
    "profiles/README.md",
    "profiles/stage0.yml",
    "profiles/base-v30.yml",
    "profiles/japanese.yml",
    "qa/README.md",
    "qa/host/README.md",
    "qa/vaeg/README.md",
    "qa/vaeg/local/README.md",
    "qa/vaeg/bios/README.md",
    "qa/vaeg/romless/README.md",
    "qa/hardware/README.md",
    "qa/fixtures/README.md",
    "qa/golden/README.md",
    "qa/tools/README.md",
    "tools/configure_component_remotes.sh",
    "tools/verify_scaffold.py",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "Makefile",
    "README.md",
}

REQUIRED_DIRS = {
    ".github",
    ".github/ISSUE_TEMPLATE",
    ".github/workflows",
    "components",
    "config",
    "config/stage0",
    "config/japanese",
    "docs",
    "docs/architecture",
    "docs/build",
    "docs/compatibility",
    "docs/decisions",
    "docs/hardware",
    "docs/licensing",
    "docs/milestones",
    "docs/provenance",
    "docs/qa",
    "images",
    "images/layouts",
    "images/output",
    "manifests",
    "mk",
    "overlays",
    "overlays/stage0",
    "overlays/japanese",
    "patches",
    "patches/fdkernel",
    "patches/freecom",
    "patches/country",
    "patches/packages",
    "profiles",
    "qa",
    "qa/host",
    "qa/vaeg",
    "qa/vaeg/local",
    "qa/vaeg/bios",
    "qa/vaeg/romless",
    "qa/hardware",
    "qa/fixtures",
    "qa/golden",
    "qa/tools",
    "tools",
    "components/fdkernel",
    "components/freecom",
    "components/country",
}

HEX40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_SUFFIXES = {
    ".rom",
    ".d88",
    ".d98",
    ".hdi",
    ".hdd",
    ".img",
    ".ima",
    ".iso",
}


class VerificationError(Exception):
    pass


def run(root: Path, *args: str) -> str:
    result = subprocess.run(
        args,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise VerificationError(f"command failed ({' '.join(args)}): {detail}")
    return result.stdout


def tracked_paths(root: Path) -> list[str]:
    return [path for path in run(root, "git", "ls-files").splitlines() if path]


def gitlink_sha(root: Path, path: str) -> str:
    lines = run(root, "git", "ls-files", "--stage", "--", path).splitlines()
    if len(lines) != 1:
        raise VerificationError(f"expected one index entry for {path}, found {len(lines)}")
    mode, sha, stage, stage_path = lines[0].split(None, 3)
    if mode != "160000" or stage != "0" or stage_path != path:
        raise VerificationError(f"{path} is not a mode 160000 gitlink")
    return sha


def verify_tree(root: Path) -> None:
    for relative in sorted(REQUIRED_DIRS):
        if not (root / relative).is_dir():
            raise VerificationError(f"missing required directory: {relative}")
    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            raise VerificationError(f"missing required file: {relative}")


def verify_gitmodules(root: Path) -> None:
    for path, expected in EXPECTED_SUBMODULES.items():
        try:
            actual_path = run(root, "git", "config", "--file", ".gitmodules", "--get", f"submodule.{path}.path").strip()
            actual_url = run(root, "git", "config", "--file", ".gitmodules", "--get", f"submodule.{path}.url").strip()
            actual_branch = run(root, "git", "config", "--file", ".gitmodules", "--get", f"submodule.{path}.branch").strip()
        except VerificationError as exc:
            raise VerificationError(f"invalid .gitmodules entry for {path}: {exc}") from exc
        if (actual_path, actual_url, actual_branch) != (path, expected["url"], expected["branch"]):
            raise VerificationError(
                f".gitmodules mismatch for {path}: "
                f"path={actual_path!r} url={actual_url!r} branch={actual_branch!r}"
            )


def verify_submodules(root: Path) -> dict[str, str]:
    status = run(root, "git", "submodule", "status", "--recursive")
    for line in status.splitlines():
        if line and line[0] in "-+U":
            raise VerificationError(f"submodule is not cleanly checked out: {line}")
    shas: dict[str, str] = {}
    for path in EXPECTED_SUBMODULES:
        sha = gitlink_sha(root, path)
        try:
            head = run(root, "git", "-C", path, "rev-parse", "--verify", "HEAD").strip()
        except VerificationError as exc:
            raise VerificationError(f"submodule is not initialized: {path}") from exc
        if not HEX40.fullmatch(head) or head != sha:
            raise VerificationError(f"{path} HEAD {head} does not match parent gitlink {sha}")
        shas[path] = sha
    return shas


def verify_lock(root: Path, shas: dict[str, str]) -> None:
    try:
        data = json.loads((root / "manifests/components.lock.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid components lock JSON: {exc}") from exc
    if data.get("schema_version") != 1 or data.get("status") != "scaffold":
        raise VerificationError("components lock must have schema_version 1 and scaffold status")
    components = data.get("components")
    if not isinstance(components, list) or len(components) != 3:
        raise VerificationError("components lock must contain exactly three components")
    seen: set[str] = set()
    expected_stability = {
        "fdkernel": "experimental",
        "freecom": "experimental-fork",
        "country": "upstream",
    }
    historical_shas: dict[str, str] = {}
    for component in components:
        if not isinstance(component, dict):
            raise VerificationError("each lock component must be an object")
        name = component.get("name")
        path = component.get("path")
        expected = EXPECTED_SUBMODULES.get(path)
        if expected is None or name != expected["name"] or name in seen:
            raise VerificationError(f"unexpected or duplicate lock component: {name!r} at {path!r}")
        seen.add(name)
        if (component.get("repository") != expected.get("lock_url", expected["url"])
                or component.get("branch") != expected["branch"]):
            raise VerificationError(f"lock provenance mismatch for {name}")
        commit = component.get("commit")
        if not isinstance(commit, str) or not HEX40.fullmatch(commit):
            raise VerificationError(f"lock commit for {name} is not a 40-character SHA")
        if component.get("stability") != expected_stability[name]:
            raise VerificationError(f"lock stability mismatch for {name}")
        historical_shas[path] = commit
    if seen != {value["name"] for value in EXPECTED_SUBMODULES.values()}:
        raise VerificationError("lock component set is incomplete")
    try:
        current_shas = resolve_current_components(root, historical_shas)
    except CurrentComponentError as exc:
        raise VerificationError(str(exc)) from exc
    if current_shas != shas:
        raise VerificationError("current component lock does not match parent gitlinks")


def verify_remotes(root: Path) -> None:
    for path, expected in EXPECTED_SUBMODULES.items():
        try:
            origin = run(root, "git", "-C", path, "remote", "get-url", "origin").strip()
        except VerificationError as exc:
            raise VerificationError(f"missing origin remote in {path}") from exc
        if origin != expected["url"]:
            raise VerificationError(f"origin URL mismatch in {path}: {origin}")
        if path == "components/country":
            continue
        # From M20 upstream is the official FreeDOS repository and lpproj is
        # the NEC PC-98/DBCS reference remote; through M19 upstream was lpproj.
        expected_remotes = {
            "components/fdkernel": {
                "upstream": "https://github.com/FDOS/kernel.git",
                "lpproj": "https://github.com/lpproj/fdkernel.git",
            },
            "components/freecom": {
                "upstream": "https://github.com/FDOS/freecom.git",
                "lpproj": "https://github.com/lpproj/freecom_dbcs2.git",
            },
        }[path]
        for name, expected_url in expected_remotes.items():
            try:
                url = run(root, "git", "-C", path, "remote", "get-url", name).strip()
            except VerificationError as exc:
                raise VerificationError(f"missing {name} remote in {path}") from exc
            if url != expected_url:
                raise VerificationError(f"{name} URL mismatch in {path}: {url}")


def verify_tracked_safety(root: Path, tracked: list[str]) -> None:
    if "config/local.env" in tracked:
        raise VerificationError("config/local.env is tracked")
    if (root / "LICENSE").exists() or "LICENSE" in tracked:
        raise VerificationError("root LICENSE must remain absent while selection is deferred")
    forbidden = []
    for path in tracked:
        lower = path.lower()
        if any(lower.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            forbidden.append(path)
        if "/__pycache__/" in lower or lower.endswith(".pyc"):
            forbidden.append(path)
        if lower.startswith(("local/", "private/")) or "pc88va-private-docs" in lower:
            forbidden.append(path)
    if forbidden:
        raise VerificationError("forbidden tracked artifacts: " + ", ".join(sorted(set(forbidden))))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    try:
        verify_tree(root)
        verify_gitmodules(root)
        shas = verify_submodules(root)
        verify_lock(root, shas)
        verify_remotes(root)
        verify_tracked_safety(root, tracked_paths(root))
    except VerificationError as exc:
        errors.append(str(exc))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("HOST PASS: M00 scaffold, gitlinks, lock metadata, remotes, and artifact policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
