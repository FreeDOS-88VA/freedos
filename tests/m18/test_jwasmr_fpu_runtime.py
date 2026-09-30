# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
from tools.m18.assembler.build_jwasmr import verify_floating_runtime


class JwasmrFpuRuntimeTests(unittest.TestCase):
    MAP = "\n".join([
        'Module: /opt/openwatcom-1.9/lib286/math87l.lib(strtod.c)',
        'Module: /opt/openwatcom-1.9/lib286/dos/emu87.lib(initemu.asm)',
        'Module: /opt/openwatcom-1.9/lib286/dos/emu87.lib(emu8087.asm)',
        'Module: /opt/openwatcom-1.9/lib286/dos/emu87.lib(dosinit.asm)',
    ])

    def test_both_conversion_and_full_emulation_are_required(self):
        verify_floating_runtime(self.MAP)
        for module in ('strtod.c', 'initemu.asm', 'emu8087.asm', 'dosinit.asm'):
            with self.subTest(module=module), self.assertRaisesRegex(ValueError, 'software 8087'):
                verify_floating_runtime(self.MAP.replace(module, 'missing.module'))
        with self.assertRaisesRegex(ValueError, 'software 8087'):
            verify_floating_runtime(self.MAP + '\n' + self.MAP)
        with self.assertRaisesRegex(ValueError, 'software 8087'):
            verify_floating_runtime(self.MAP + '\nModule: /opt/lib286/dos/noemu87.lib(fake)')


if __name__ == '__main__':
    unittest.main()
