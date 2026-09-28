# SPDX-License-Identifier: GPL-2.0-or-later
"""M17-local component remote setup and provenance checks."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / 'tools/m17'))
from component_remotes import REMOTES, configure


class ComponentRemoteTests(unittest.TestCase):
    @staticmethod
    def git(path, *args):
        return subprocess.run(['git', '-C', str(path), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True).stdout.strip()

    def root_with_components(self, root):
        for name in REMOTES:
            path = root / 'components' / name
            path.mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', str(path)], check=True)
        return root

    def test_missing_remotes_are_added_once_and_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.root_with_components(Path(directory))
            with self.assertRaises(ValueError):
                configure(root)
            configure(root, add_missing=True)
            configure(root)
            for name, expected in REMOTES.items():
                path = root / 'components' / name
                for remote, url in expected.items():
                    self.assertEqual(self.git(path, 'remote', 'get-url', remote), url)
                self.assertEqual(self.git(path, 'remote', 'get-url', '--push', 'origin'),
                                 expected['origin'])

    def test_mismatched_existing_remote_fails_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.root_with_components(Path(directory))
            path = root / 'components/fdkernel'
            self.git(path, 'remote', 'add', 'origin', 'https://example.invalid/fdkernel.git')
            with self.assertRaises(ValueError):
                configure(root, add_missing=True)
            self.assertEqual(self.git(path, 'remote', 'get-url', 'origin'),
                             'https://example.invalid/fdkernel.git')


if __name__ == '__main__':
    unittest.main()
