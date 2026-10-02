# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class MemmapRuntimeTests(unittest.TestCase):
    def test_prime_then_ownership_aware_trim_then_walk_or_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            program = Path(directory) / 'runtime-test'
            subprocess.run([
                'cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                '-I', str(ROOT / 'tests/m19/memmap_stubs'),
                '-I', str(ROOT / 'tools/m19/memmap'),
                str(ROOT / 'tests/m19/memmap_runtime_test.c'),
                str(ROOT / 'tools/m19/memmap/mcb_parser.c'), '-o', str(program),
            ], check=True)
            result = subprocess.run([str(program)], check=True, capture_output=True, text=True)
            self.assertEqual(result.stdout.count('MCB chain: VALID'), 1)
            self.assertEqual(result.stderr.count('unable to trim unused runtime heap safely'), 2)


if __name__ == '__main__':
    unittest.main()
