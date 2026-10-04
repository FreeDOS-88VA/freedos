# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pc_baseline", ROOT / "tools/m20/pc_baseline.py")
pc_baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc_baseline)


class PcBaselineTests(unittest.TestCase):
    def test_only_embedded_build_timestamps_are_ignored(self):
        a = b"\x90code[Oct  3 2026 21:46:17]tail\x00"
        self.assertTrue(pc_baseline.same_except_timestamps(a, a))
        self.assertTrue(pc_baseline.same_except_timestamps(
            a, b"\x90code[Feb 22 2025 14:17:52]tail\x00"))
        for other in (b"\x91code[Oct  3 2026 21:46:17]tail\x00",
                      b"\x90code[Oct  3 2026 21:46:17]tAil\x00",
                      a + b"\x00"):
            with self.subTest(other=other):
                self.assertFalse(pc_baseline.same_except_timestamps(a, other))


if __name__ == "__main__":
    unittest.main()
