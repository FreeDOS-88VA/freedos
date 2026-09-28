#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Source contract checks for the pinned PC-88VA FreeCOM target."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
FREECOM = ROOT / 'components' / 'freecom'


def target_branch(source, marker, end_marker):
    start = source.index(marker)
    end = source.index(end_marker, start + len(marker))
    return source[start:end]


class FreecomInputSourceTests(unittest.TestCase):
    def test_build_target_enables_enhanced_input_and_excludes_other_machines(self):
        script = (FREECOM / 'build.sh').read_text()
        target = target_branch(script, '    pc88va)', '    ibmpc)')
        self.assertIn('unset GENDOS', target)
        self.assertIn('unset IBMPC', target)
        self.assertIn('unset NEC98', target)
        self.assertIn('unset NO_ENH_INP', target)
        self.assertIn('export PC88VA=1', target)

        config = (FREECOM / 'config.std').read_text()
        self.assertIn('!if $(PC88VA)0 == 10\n__TARGET = -DPC88VA', config)

    def test_dos_extended_bytes_are_consumed_as_one_freecom_scan_code(self):
        source = (FREECOM / 'lib' / 'cgetch.c').read_text()
        target = target_branch(source, '#elif defined(PC88VA)', '#else /* IBMPC or generic DOS */')
        self.assertIn('regs.r_ax = 0x0700', target)
        self.assertIn('intrpt(0x21, &regs)', target)
        self.assertIn('if (c == 0)', target)
        self.assertIn('SCANCODE(pc88va_dos_getch())', target)
        self.assertIn('if (c == KEY_CTL_C)', target)
        self.assertNotIn('int 10h', target.lower())
        self.assertNotIn('int 16h', target.lower())

    def test_va_and_va2_common_key_codes_and_documented_extensions(self):
        source = (FREECOM / 'include' / 'keys.h').read_bytes().decode('latin1').replace('\r\n', '\n')
        target = target_branch(source, '#elif defined(PC88VA)', '#else /* IBMPC */')
        definitions = {line.split()[1]: line for line in target.splitlines()
                       if line.startswith('#define ')}
        for key, code in [('KEY_F1', '0x3b'), ('KEY_F10', '0x44'),
                          ('KEY_UP', '0x48'), ('KEY_DOWN', '0x50'),
                          ('KEY_LEFT', '0x4b'), ('KEY_RIGHT', '0x4d'),
                          ('KEY_HOME', '0x47'), ('KEY_END', '0x4f'),
                          ('KEY_INSERT', '0x52'), ('KEY_DELETE', '0x53'),
                          ('KEY_CTRL_LEFT', '0x73'), ('KEY_CTRL_RIGHT', '0x74')]:
            with self.subTest(key=key):
                self.assertTrue(definitions[key].endswith(f'SCANCODE({code})'))
        for key, code in [('KEY_SHIFT_F1', '0x80'), ('KEY_SHIFT_F10', '0x89'),
                          ('KEY_SHIFT_UP', '0x8a'), ('KEY_SHIFT_RIGHT', '0x8d')]:
            self.assertTrue(definitions[key].endswith(f'SCANCODE({code})'))

    def test_native_cursor_reads_sets_position_and_keeps_cursor_visible(self):
        cmdinput = (FREECOM / 'lib' / 'cmdinput.c').read_text()
        position = target_branch(cmdinput, '#elif defined(PC88VA)', '#elif defined(IBMPC)')
        self.assertEqual(position.count('r.r_ax = 0x2e00'), 2)
        self.assertIn('((r.r_dx >> 8) & 0xff)', position)
        self.assertIn('(r.r_dx & 0xff)', position)

        style = target_branch(cmdinput,
                              '#elif defined(PC88VA)\n\nstatic void setcursorstate_pc88va',
                              '#elif defined(IBMPC)')
        self.assertIn('r.r_ax = insert ? 0x2513 : 0x2503', style)
        self.assertIn('intrpt(0x83, &r)', style)

        goxy = (FREECOM / 'lib' / 'goxy.c').read_text()
        position = target_branch(goxy, '#elif defined(PC88VA)', '#elif defined(IBMPC)')
        self.assertIn('r.r_ax = 0x0800', position)
        self.assertIn('r.r_dx = ((unsigned)column << 8) | row', position)
        self.assertIn('intrpt(0x83, &r)', position)
        self.assertNotIn('int 10h', position.lower())


if __name__ == '__main__':
    unittest.main()
