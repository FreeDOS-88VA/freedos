#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Configure/check the exact public remotes for M17's pinned components."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REMOTES = {
    'fdkernel': {
        'origin': 'https://github.com/nakatamaho/fdkernel.git',
        'upstream': 'https://github.com/lpproj/fdkernel.git',
    },
    'freecom': {
        'origin': 'https://github.com/nakatamaho/freecom_dbcs2.git',
        'upstream': 'https://github.com/lpproj/freecom_dbcs2.git',
    },
    'country': {
        'origin': 'https://github.com/FDOS/country.git',
    },
}


def _git(path, *args, check=True):
    return subprocess.run(['git', '-C', str(path), *args], check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True).stdout.strip()


def configure(root=ROOT, add_missing=False):
    root = Path(root).resolve()
    for name, expected_remotes in REMOTES.items():
        path = root / 'components' / name
        if not path.is_dir() or _git(path, 'rev-parse', '--show-toplevel') != str(path):
            raise ValueError('component checkout is not initialized: ' + name)
        names = set(_git(path, 'remote').splitlines())
        for remote, expected in expected_remotes.items():
            if remote in names:
                actual = _git(path, 'remote', 'get-url', remote)
                if actual != expected:
                    raise ValueError(f'{name} {remote} is {actual}, expected {expected}')
            elif add_missing:
                _git(path, 'remote', 'add', remote, expected)
            else:
                raise ValueError(f'{name} is missing expected remote {remote}')
        push_url = _git(path, 'remote', 'get-url', '--push', 'origin')
        if push_url != expected_remotes['origin']:
            raise ValueError(f'{name} origin push URL is not the public fork')
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--configure', action='store_true',
                        help='add a missing expected remote; never replace a mismatched one')
    args = parser.parse_args(argv)
    configure(args.root, add_missing=args.configure)
    print('M17 component remotes verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
