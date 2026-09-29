# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the production 8086 far-call adapter with DOS return semantics."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
from unicorn.x86_const import (
    UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_DX,
    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_BP, UC_X86_REG_SP,
    UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS,
    UC_X86_REG_EFLAGS,
)

ROOT = Path(__file__).resolve().parents[2]


class DiskAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / 'tools/m18/maintenance/diskio.asm').read_text()
        source = '\n'.join(line for line in source.splitlines()
                           if not line.startswith(('segment ', 'global ')))
        with tempfile.TemporaryDirectory() as directory:
            assembly = Path(directory) / 'adapter.asm'
            binary = Path(directory) / 'adapter.bin'
            assembly.write_text(source)
            subprocess.run(['nasm', '-f', 'bin', str(assembly), '-o', str(binary)],
                           check=True)
            cls.code = binary.read_bytes()

    def test_live_carry_not_discarded_original_flags(self):
        for writing in (0, 1):
            for carry, original_carry, error in ((0, 1, 0x1234),
                                                (1, 0, 0x0201),
                                                (1, 0, 0)):
                with self.subTest(writing=writing, carry=carry, error=error):
                    uc = Uc(UC_ARCH_X86, UC_MODE_16)
                    uc.mem_map(0, 0x100000)
                    uc.mem_write(0x10000, self.code)
                    registers = {
                        UC_X86_REG_CS: 0x1000, UC_X86_REG_SS: 0x5000,
                        UC_X86_REG_SP: 0x8000, UC_X86_REG_DS: 0x2000,
                        UC_X86_REG_ES: 0x3000, UC_X86_REG_BP: 0x7890,
                        UC_X86_REG_BX: 0x1234, UC_X86_REG_CX: 0x2345,
                        UC_X86_REG_DX: 0x3456, UC_X86_REG_SI: 0x4567,
                        UC_X86_REG_DI: 0x5678,
                    }
                    for register, value in registers.items():
                        uc.reg_write(register, value)
                    uc.mem_write(0x58000, struct.pack('<7H',
                                 0x800, 0x1000, writing, 1, 9, 0x234, 0x4000))
                    calls = []

                    def interrupt(machine, number, _):
                        calls.append(number)
                        self.assertEqual(number, 0x26 if writing else 0x25)
                        for register, value in ((UC_X86_REG_AX, 1),
                                                (UC_X86_REG_DX, 9),
                                                (UC_X86_REG_CX, 1),
                                                (UC_X86_REG_DS, 0x4000),
                                                (UC_X86_REG_BX, 0x234)):
                            self.assertEqual(machine.reg_read(register), value)
                        # INT 25h/26h return via RETF, leaving the caller's
                        # original FLAGS on the stack, but result CF live.
                        sp = machine.reg_read(UC_X86_REG_SP) - 2
                        machine.reg_write(UC_X86_REG_SP, sp)
                        machine.mem_write(0x50000 + sp,
                                          struct.pack('<H', 0x202 | original_carry))
                        machine.reg_write(UC_X86_REG_AX, error)
                        machine.reg_write(UC_X86_REG_EFLAGS, 0x202 | carry)

                    uc.hook_add(UC_HOOK_INTR, interrupt)
                    uc.emu_start(0x10000, 0x10800, count=100)
                    self.assertEqual(len(calls), 1)
                    self.assertEqual(uc.reg_read(UC_X86_REG_AX),
                                     (error or 1) if carry else 0)
                    for register, value in registers.items():
                        if register == UC_X86_REG_SP:
                            value += 4  # Far return consumes IP and CS only.
                        self.assertEqual(uc.reg_read(register), value)


if __name__ == '__main__':
    unittest.main()
