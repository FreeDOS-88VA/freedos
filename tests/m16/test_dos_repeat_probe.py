#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keep the guest-timed repeat probe bounded and host-inspectable."""
from pathlib import Path
import json
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

    def test_editing_repeat_fixture_keeps_complete_extended_events(self):
        script = (ROOT / 'tests/m16/dos_repeat_editing.script').read_text()
        contract = json.loads((ROOT / 'tests/m16/dos_repeat_editing_sequence.json').read_text())
        self.assertEqual(re.findall(r'^@hold .*', script, re.MULTILINE),
                         ['@hold backspace 90', '@hold left 90', '@hold right 38'])
        expected = b'q' + b'\x08' * 16 + b'\x00\x4b' * 16 + b'\x00\x4d' * 3 + b'c'
        self.assertEqual(bytes.fromhex(contract['bytes_hex']), expected)
        self.assertLessEqual(len(expected), 128)
        self.assertTrue(script.endswith('@enter\n'))

    def test_script_uses_a_guest_time_hold_and_separate_repress(self):
        script = (ROOT / 'tests/m16/dos_repeat_probe.script').read_text().splitlines()
        commands = [line.strip() for line in script
                    if line.strip() and not line.lstrip().startswith('#')]
        self.assertEqual(commands[:4], ['@wait 240', '@enter', '@enter', 'DOSREPT'])
        self.assertEqual(commands[4:6], ['@wait 240', '@text q'])
        contract = json.loads((ROOT / 'tests/m16/dos_repeat_sequence.json').read_text())
        self.assertEqual(contract['schema_version'], 1)
        self.assertEqual(contract['clock']['initial_delay_edges'], 30)
        self.assertEqual(contract['clock']['repeat_period_edges'], 4)
        self.assertEqual([line for line in commands if line.startswith('@hold ')],
                         [f"@hold a {contract['inputs']['held_a']['guest_frames']}",
                          f"@hold b {contract['inputs']['held_b']['guest_frames']}"])
        self.assertEqual(commands[6], '@wait 120')
        self.assertEqual(commands[8:11], ['@wait 120', '@text c', '@wait 120'])
        second_hold = commands.index(
            f"@hold b {contract['inputs']['held_b']['guest_frames']}")
        self.assertEqual(commands[second_hold - 1], '@wait 120')
        self.assertEqual(commands[-1], '@enter')
        self.assertGreaterEqual(len(re.findall(r'^@wait ', '\n'.join(commands), re.MULTILINE)), 3)
        expected = (b'q' + b'a' * contract['inputs']['held_a']['events'] + b'c' +
                    b'b' * contract['inputs']['held_b']['events'])
        self.assertEqual(bytes.fromhex(contract['bytes_hex']), expected)


if __name__ == '__main__':
    unittest.main()
