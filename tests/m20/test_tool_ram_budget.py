# SPDX-License-Identifier: GPL-2.0-or-later
import struct
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m20/qa'))
from tool_ram_budget import mz_exec_floor, all_tool_floors, TOOLS


class ToolRamBudgetTests(unittest.TestCase):
    def sample(self):
        header = [0x5a4d, 400, 2, 0, 2, 0, 0xffff, 0x35, 0,
                  0, 0, 0, 0x1c, 0]
        data = bytearray(912)
        struct.pack_into('<14H', data, 0, *header)
        return data

    def test_loader_rounds_final_page_and_does_not_conflate_heap_peak(self):
        budget = mz_exec_floor(self.sample())
        self.assertEqual(budget['mz_real_image_bytes'], 880)
        self.assertEqual(budget['mz_real_image_paragraphs'], 55)
        self.assertEqual(budget['dos_loader_rounded_image_paragraphs'], 62)
        self.assertEqual(budget['page_rounding_extra_paragraphs'], 7)
        self.assertEqual(budget['minimum_psp_block_bytes'], (16 + 62)*16)
        self.assertIn('peaks are excluded', budget['scope'])

    def test_drift_and_bad_entry_fail_closed(self):
        sample = self.sample()
        for offset, value, message in (
            (0, 0, 'signature'),
            (2, 0, 'file'),
            (4, 1, 'file'),
            (6, 2, 'relocation'),
            (14, 0x40, 'stack'),
            (20, 0xffff, 'entry'),
        ):
            mutated = bytearray(sample)
            if offset in (6, 14, 20):
                struct.pack_into('<H', mutated, offset, value)
            else:
                mutated[offset] = value
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, message):
                mz_exec_floor(mutated)
        with self.assertRaisesRegex(ValueError, 'mandatory'):
            all_tool_floors({name: sample for name in TOOLS[:-1]})


if __name__ == '__main__':
    unittest.main()
