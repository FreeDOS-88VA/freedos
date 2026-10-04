#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""First-pass M20 inventory of component commits above the FreeDOS 1.4 baseline.

Reads only Git history of a component checkout. Each non-merge commit in
BASE..TIP is classified mechanically by its touched paths and by whether its
stable patch-id equals an official upstream commit after BASE. The result is
a review aid, not an import decision: every import still needs the recorded
human classification required by AGENTS.md.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

# Path prefixes owned by one platform. Everything else is shared code.
PC88VA_PREFIXES = ("pc88va/", "sys/pc88va.c")
PC98_PREFIXES = ("nec98/", "NEC98.txt")
# Build/platform scaffolding introduced by the PC-98 work to host several
# platforms in one tree. Separated from shared DOS code for review.
PLATFORM_PREFIXES = ("template/", "ibmpc/")
META_PREFIXES = (".github/", ".gitignore", ".gitattributes", "README", "docs/",
                 "ci_build.sh", "ci_prereq.sh", "tests/kswap/")
# Platform selectors counted in added lines; FreeCOM keeps platform code in
# shared files, so paths alone do not identify it.
MARKERS = ("PC88VA", "NEC98", "DBCS")


def git(repo: Path, *args: str) -> str:
    # Component history contains Shift-JIS text; decode losslessly enough for
    # path, marker and statistics analysis.
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True).stdout.decode("utf-8", "replace")


def patch_id(repo: Path, commit: str) -> str | None:
    show = subprocess.run(["git", "-C", str(repo), "show", commit],
                          check=True, capture_output=True).stdout
    out = subprocess.run(["git", "-C", str(repo), "patch-id", "--stable"],
                         input=show, check=True, capture_output=True).stdout
    return out.split()[0].decode("ascii") if out.strip() else None


def area(path: str) -> str:
    if path.startswith(PC88VA_PREFIXES):
        return "pc88va"
    if path.startswith(PC98_PREFIXES):
        return "pc98"
    if path.startswith(PLATFORM_PREFIXES):
        return "platform"
    if path.startswith(META_PREFIXES):
        return "meta"
    return "shared"


def classify(areas: set[str], upstream: bool) -> str:
    if upstream:
        return "upstream-backport"
    code = areas - {"meta"}
    if not code:
        return "meta-only"
    if code == {"pc88va"}:
        return "pc88va-only"
    if code == {"pc98"}:
        return "pc98-only"
    if code <= {"platform", "pc98", "pc88va"}:
        return "platform-scaffolding"
    return "touches-shared"


def inventory(repo: Path, base: str, tip: str, upstream: str) -> list[dict]:
    upstream_ids = {}
    for commit in git(repo, "rev-list", "--no-merges", f"{base}..{upstream}").split():
        pid = patch_id(repo, commit)
        if pid:
            upstream_ids[pid] = commit
    ancestors = set(git(repo, "rev-list", f"{base}..{upstream}").split())
    rows = []
    for line in git(repo, "log", "--reverse", "--no-merges",
                    "--format=%H%x09%an%x09%ad%x09%s", "--date=short",
                    f"{base}..{tip}").splitlines():
        commit, author, date, subject = line.split("\t", 3)
        paths = [p for p in git(repo, "diff-tree", "--no-commit-id", "--name-only",
                                "-r", commit).splitlines() if p]
        areas = {area(p) for p in paths}
        stat = git(repo, "diff-tree", "--no-commit-id", "--numstat", "-r", commit)
        added = deleted = shared_lines = 0
        for entry in stat.splitlines():
            a, d, p = entry.split("\t", 2)
            if a == "-":
                continue
            added += int(a)
            deleted += int(d)
            if area(p) == "shared":
                shared_lines += int(a) + int(d)
        diff = git(repo, "show", "--format=", "--unified=0", commit)
        added_text = "\n".join(l for l in diff.splitlines()
                               if l.startswith("+") and not l.startswith("+++"))
        markers = {m: len(re.findall(r"\b" + m + r"\b", added_text)) for m in MARKERS}
        pid = patch_id(repo, commit)
        match = commit if commit in ancestors else upstream_ids.get(pid or "")
        rows.append({
            "commit": commit, "author": author, "date": date, "subject": subject,
            "class": classify(areas, match is not None),
            "upstream_commit": match, "areas": sorted(areas),
            "added": added, "deleted": deleted, "shared_lines": shared_lines,
            "markers": {m: n for m, n in markers.items() if n},
            "shared_paths": sorted(p for p in paths if area(p) == "shared"),
        })
    return rows


def markdown(rows: list[dict]) -> str:
    out = ["| Commit | Date | Author | Class | +/- | Shared lines | Markers | Subject |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        subject = r["subject"].replace("|", "\\|")[:100]
        markers = " ".join(f"{k}:{v}" for k, v in r["markers"].items())
        out.append(f"| `{r['commit'][:10]}` | {r['date']} | {r['author']} | "
                   f"{r['class']} | +{r['added']}/-{r['deleted']} | "
                   f"{r['shared_lines']} | {markers} | {subject} |")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--base", required=True, help="baseline commit, e.g. ke2043")
    parser.add_argument("--tip", required=True, help="commit to inventory")
    parser.add_argument("--upstream", required=True,
                        help="official upstream ref used for patch-id matching")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    rows = inventory(args.repo, args.base, args.tip, args.upstream)
    if args.json:
        args.json.write_text(json.dumps(rows, indent=2) + "\n")
    if args.markdown:
        args.markdown.write_text(markdown(rows))
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    print(json.dumps({"commits": len(rows), "classes": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
