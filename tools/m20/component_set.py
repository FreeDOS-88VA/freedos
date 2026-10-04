#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Single source of the M20 component set: manifests/m20-components.lock.json.

The core components are always required; additional components (floppy-set
programs and their libraries) are taken from the lock in its order.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
LOCK = Path("manifests/m20-components.lock.json")
CORE = ("fdkernel", "freecom", "country", "edlin", "jwasm")
NAME = re.compile(r"[a-z0-9][a-z0-9_-]*")


def locked_names(root: Path = ROOT) -> tuple[str, ...]:
    document = json.loads((root / LOCK).read_text(encoding="ascii"))
    names = tuple(item.get("name") for item in document.get("components", []))
    if (len(set(names)) != len(names) or not all(isinstance(n, str) and NAME.fullmatch(n) for n in names)
            or not set(CORE) <= set(names)):
        raise ValueError("M20 component lock has an invalid component set")
    for item in document["components"]:
        if item.get("path") != "components/" + item["name"]:
            raise ValueError("M20 component path differs from its name: " + item["name"])
    return names


if __name__ == "__main__":
    print(" ".join(locked_names()))
