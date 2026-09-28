#!/usr/bin/env python3
"""Test M01 image identity and cleanup decisions without using Docker."""

import re
from pathlib import Path


DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def cleanup_decision(container_id, retain):
    if not container_id:
        return "noop"
    if DIGEST.fullmatch(container_id) is None:
        return "refuse"
    if retain:
        return "retain"
    return "remove-exact-id"


def main():
    root = Path(__file__).resolve().parents[2]
    harness = (root / "tools/m01/build_baseline.sh").read_text(encoding="utf-8")
    image_block = harness[harness.index("record_image() {"):harness.index("\nimage() {", harness.index("record_image() {"))]
    build_block = harness[harness.index("build() {"):harness.index("\ncompare() {", harness.index("build() {"))]
    preflight_block = harness[harness.index("preflight() {"):harness.index("\ndownload_verified_openwatcom() {", harness.index("preflight() {"))]

    equal = "sha256:" + "a" * 64
    unequal = "sha256:" + "b" * 64
    assert DIGEST.fullmatch(equal)
    assert DIGEST.fullmatch(unequal)
    assert equal != unequal
    for malformed in ("", "sha256:" + "A" * 64, "sha256:" + "a" * 63, "sha256:" + "a" * 65, "sha256:" + "a" * 64 + " "):
        assert DIGEST.fullmatch(malformed) is None

    assert 'docker image inspect "$image_reference" --format \'{{.Id}}\'' in image_block
    assert 'docker buildx imagetools inspect "$M01_BASE_IMAGE@$M01_BASE_INDEX_DIGEST"' in preflight_block
    assert 'docker image inspect "$M01_IMAGE_TAG" >/dev/null 2>&1' in build_block
    assert 'docker image inspect --platform "$M01_PLATFORM" "$M01_IMAGE_TAG"' not in build_block
    assert '"$resolved_local_image_config_id" /input/image_tool_probe.sh' in image_block
    assert '"$M01_IMAGE_TAG" /input/image_tool_probe.sh' not in image_block
    assert "wait_status=0" in image_block
    assert "wait_output=$(docker wait" in image_block
    probe_script = (root / "tools/m01/container/image_tool_probe.sh").read_text(encoding="utf-8")
    assert probe_script.startswith("#!/bin/sh\n")
    assert not re.search(r"^\s*type\s+-a(?:\s|$)", probe_script, re.MULTILINE)
    assert "grep -E 'F38|E02|Error\\('" in probe_script
    assert "container_runtime_image_config_id" in harness
    assert "resolved_local_image_config_id" in harness
    assert "container_config_image_reference" in harness
    assert "container_runtime_image_config_id != resolved_local_image_config_id" in harness
    assert "local_image_id" not in image_block
    assert "${probe_container_id:-}" in harness
    assert 'docker rm "$cleanup_id"' in harness

    assert cleanup_decision("", 0) == "noop"
    assert cleanup_decision(None, 0) == "noop"
    assert cleanup_decision("not-an-id", 0) == "refuse"
    assert cleanup_decision(equal, 1) == "retain"
    assert cleanup_decision(equal, 0) == "remove-exact-id"

    print("image identity regression passed: strict IDs, resolved create input, runtime equality, and unset-safe cleanup")


if __name__ == "__main__":
    main()
