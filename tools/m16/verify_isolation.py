#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Require an exported M16 build to contain no other milestone directories."""
from pathlib import Path
import re
import argparse

ROOT = Path(__file__).resolve().parents[2]


def verify(root):
    for category in ('tools', 'tests', 'config', 'containers'):
        for entry in (root / category).glob('m[0-9][0-9]'):
            if entry.name != 'm16':
                raise ValueError('Historical milestone directory in isolated build: ' + str(entry))
    for path in (root / 'tools/m16').rglob('*'):
        if path.is_symlink():
            raise ValueError('M16 runtime tooling cannot contain symlinks: ' + str(path))
        if path.suffix in ('.py', '.sh') or path.name == 'Dockerfile':
            source = path.read_text()
            if re.search(r'(?:tools|tests|config|containers)/m(?!16)[0-9]{2}(?:/|\b)', source):
                raise ValueError('Cross-milestone runtime path in ' + str(path))
            component_helper = ('components/fdkernel/pc88va/' +
                                r'(?:tools|tests)(?:/|\b)')
            if re.search(component_helper, source):
                raise ValueError('M16 tooling imports component helper/test code: ' + str(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    verify(args.root.resolve())
    print('M16 build export is isolated from other milestones')
