# SPDX-License-Identifier: GPL-2.0-or-later
"""Non-bootable M20 data disks for drive B: and their record names.

Each disk is declared by its own configuration. Its records use the kind as
a prefix: build output ``<stem>.d88`` and ``<kind>-manifest.json``, build
manifest fields ``<kind>_d88`` and ``<kind>_manifest_sha256``, and two-build
fields ``<kind>_d88_byte_identical``, ``<kind>_d88_sha256`` and
``release_<kind>_records_identical``.
"""
from __future__ import annotations

DATA_DISKS: dict[str, dict[str, str]] = {
    "utility": {"config": "config/m20/utility-disk.json", "stem": "util",
                "title": "utilities"},
    "archive": {"config": "config/m20/archive-disk.json", "stem": "archive",
                "title": "archiver"},
}


def manifest_fields() -> set[str]:
    return {name for kind in DATA_DISKS for name in (kind + "_d88", kind + "_manifest_sha256")}


def comparison_fields() -> set[str]:
    return {name for kind in DATA_DISKS for name in (
        kind + "_d88_byte_identical", kind + "_d88_sha256", "release_" + kind + "_records_identical")}
