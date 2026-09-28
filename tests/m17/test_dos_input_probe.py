#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keep the public DOS input probe, contract and normal-input script aligned."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DosInputProbeTests(unittest.TestCase):
    def test_probe_length_matches_expected_guest_bytes(self):
        source = (ROOT / 'tests/m17/dos_input_probe.asm').read_text()
        contract = json.loads((ROOT / 'tests/m17/dos_input_sequence.json').read_text())
        match = re.search(r'^%define INPUT_BYTES (\d+)$', source, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), len(bytes.fromhex(contract['bytes_hex'])))
        self.assertIn("mov ah, 07h", source)
        self.assertIn("output_name db 'KEYINPUT.BIN',0", source)

    def test_script_produces_one_key_event_per_expected_event_group(self):
        script = (ROOT / 'tests/m17/dos_input_probe.script').read_text().splitlines()
        commands = [line.strip() for line in script
                    if line.strip() and not line.lstrip().startswith('#')]
        self.assertEqual(len(commands), 41)
        self.assertEqual(commands[:6], ['@wait 240', '@enter', '@enter', 'DOSINPUT',
                                        '@text q', '@key ctrl-c'])
        self.assertEqual(commands[6], '@enter')
        self.assertEqual(commands[7:17], [f'@key f{i}' for i in range(1, 11)])
        self.assertEqual(commands[17:27], [f'@key shift-f{i}' for i in range(1, 11)])
        self.assertEqual(commands[-1], '@key shift-right')


if __name__ == '__main__':
    unittest.main()
