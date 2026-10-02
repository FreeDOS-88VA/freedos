# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
from unicorn.x86_const import (
    UC_X86_REG_AX, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES,
    UC_X86_REG_SS, UC_X86_REG_SP,
)

ROOT = Path(__file__).resolve().parents[2]


class ExecChildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as directory:
            cls.images = {}
            for name, definitions in (('COM', []), ('EXE', ['-dM19_MZ=1'])):
                path = Path(directory) / ('CHILD.' + name)
                subprocess.run(['nasm', '-f', 'bin', *definitions,
                                str(ROOT / 'tools/m19/qa/child.asm'), '-o', str(path)],
                               check=True)
                cls.images[name] = path.read_bytes()

    def execute(self, data, segment, offset, stack):
        uc = Uc(UC_ARCH_X86, UC_MODE_16)
        uc.mem_map(0, 0x100000)
        for register in (UC_X86_REG_CS, UC_X86_REG_SS):
            uc.reg_write(register, segment)
        for register in (UC_X86_REG_DS, UC_X86_REG_ES):
            uc.reg_write(register, segment - 16)
        uc.reg_write(UC_X86_REG_SP, stack)
        address = segment * 16 + offset
        uc.mem_write(address, bytes(data))
        exits = []

        def interrupt(machine, number, _):
            self.assertEqual(number, 0x21)
            ax = machine.reg_read(UC_X86_REG_AX)
            self.assertEqual(ax >> 8, 0x4c)
            exits.append(ax & 255)
            machine.emu_stop()

        uc.hook_add(UC_HOOK_INTR, interrupt)
        uc.emu_start(address, 0xfffff, count=1000)
        self.assertEqual(len(exits), 1)
        return exits[0]

    def load_com_frame(self, data):
        # task.c:load_transfer writes hdr/pcb.h's twelve-word iregs BEFORE
        # executing the COM entry point. Merely decoding the file misses this.
        stack = 0x100 + len(data) - 2
        frame = struct.pack('<12H', 0, 0, 0xff, 0x2000, 0x100, stack,
                            0x91e, 0x2000, 0x2000, 0x100, 0x2000, 0x200)
        frame_offset = stack - len(frame) - 0x100
        if frame_offset < 5:
            raise ValueError('initial DOS register frame overlaps live COM code')
        loaded = bytearray(data)
        loaded[frame_offset:frame_offset + len(frame)] = frame
        return loaded, stack

    def test_com_has_owned_startup_stack_and_real_exit_code(self):
        data = self.images['COM']
        self.assertEqual(len(data), 128)
        loaded, stack = self.load_com_frame(data)
        self.assertEqual(loaded[:5], data[:5])
        self.assertEqual(self.execute(loaded, 0x2000, 0x100, stack), 42)
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            self.load_com_frame(data[:16])

    def test_mz_requires_relocation_and_has_bounded_live_stack(self):
        data = self.images['EXE']
        header = struct.unpack_from('<14H', data)
        self.assertEqual(header[0], 0x5a4d)
        self.assertEqual((header[2] - 1) * 512 + header[1], len(data))
        self.assertEqual(header[3:7], (1, 4, 32, 32))
        self.assertEqual(header[7], 0)
        self.assertEqual(header[10:12], (0, 0))
        module = bytearray(data[header[4] * 16:])
        self.assertGreaterEqual(header[8], len(module) + 64)
        self.assertLess(header[8], ((len(module) + 15) // 16 + header[5]) * 16)
        offset, segment = struct.unpack_from('<HH', data, header[12])
        self.assertEqual(segment, 0)
        self.assertEqual(struct.unpack_from('<H', module, offset)[0], 0)
        self.assertEqual(self.execute(module, 0x2010, 0, header[8]), 1)
        struct.pack_into('<H', module, offset, 0x2010)
        self.assertEqual(self.execute(module, 0x2010, 0, header[8]), 42)


if __name__ == '__main__':
    unittest.main()
