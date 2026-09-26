#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keep the guest-timed repeat probe bounded and host-inspectable."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DosRepeatProbeTests(unittest.TestCase):
    def test_probe_captures_until_return_and_bounds_storage(self):
        source = (ROOT / 'tests/m16/dos_repeat_probe.asm').read_text()
        self.assertIn('%define INPUT_CAPACITY 128', source)
        self.assertIn('mov ah, 07h', source)
        self.assertIn('cmp al, 0dh', source)
        self.assertIn('cmp bx, INPUT_CAPACITY', source)
        self.assertIn("output_name db 'REPEAT.BIN',0", source)
        self.assertIn('mov ah, 3ch', source)
        self.assertIn('mov ah, 40h', source)
        self.assertIn('mov ah, 3eh', source)

    def test_script_uses_a_guest_time_hold_and_separate_repress(self):
        script = (ROOT / 'tests/m16/dos_repeat_probe.script').read_text().splitlines()
        commands = [line.strip() for line in script
                    if line.strip() and not line.lstrip().startswith('#')]
        self.assertEqual(commands[:4], ['@wait 240', '@enter', '@enter', 'DOSREPT'])
        self.assertEqual([line for line in commands if line.startswith('@hold ')],
                         ['@hold a 90', '@hold b 38'])
        second_hold = commands.index('@hold b 38')
        self.assertEqual(commands[second_hold - 1], '@wait 120')
        self.assertEqual(commands[-1], '@enter')
        self.assertGreaterEqual(len(re.findall(r'^@wait ', '\n'.join(commands), re.MULTILINE)), 3)


if __name__ == '__main__':
    unittest.main()
