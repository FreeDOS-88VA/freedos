#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keep the production FreeCOM editor and history probe sequence explicit."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DosFreecomEditorTests(unittest.TestCase):
    def test_script_edits_a_valid_command_then_uses_f3_history(self):
        lines = (ROOT / 'tests/m17/dos_freecom_editor.script').read_text().splitlines()
        commands = [line.strip() for line in lines
                    if line.strip() and not line.lstrip().startswith('#')]
        self.assertEqual(commands[:4], ['@wait 240', '@enter', '@enter', '@text DIXR A:'])
        self.assertEqual(commands[4:9], ['@key home', '@key right', '@key right',
                                        '@wait 120', '@key delete'])
        self.assertEqual(commands[9:14], ['@key help', '@key backspace', '@text :',
                                         '@enter', '@wait 600'])
        self.assertEqual(commands[14:18], ['@key f3', '@wait 90', '@enter', '@wait 600'])
        self.assertEqual(commands[18:24], ['@key f1', '@wait 90', '@key f3',
                                           '@wait 90', '@enter', '@wait 600'])
        self.assertEqual(commands[24:], ['@text DIR B:', '@key f5', '@wait 90',
                                        '@key f3', '@wait 90', '@enter', '@wait 600'])


if __name__ == '__main__':
    unittest.main()
