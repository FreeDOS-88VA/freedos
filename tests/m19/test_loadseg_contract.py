#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Execute the real pre-kernel selector; the file buffer must remain fixed."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m19'))
from loader_profile import nasm_definitions

class LoadSegmentTests(unittest.TestCase):
    def test_config_selects_layout_without_moving_file_staging(self):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
        from unicorn import x86_const as r
        profile = json.loads((ROOT / 'config/m19/loader.json').read_text())
        source = '''bits 16
cpu 8086
%define PC88VA_RUNTIME_LOADSEG 1
%include "loader_abi.inc"
dw pc88va_stage2_config_bootstrap, pc88va_cfg_value
dw pc88va_stage2_config_file, pc88va_stage2_file, pc88va_stage2_mz
dw FL_SEGMENT, FL_OFFSET, FL_FILE_BYTES, MZ_FILE_SEGMENT
%include "config_probe.inc"
pc88va_file_load_core: xor ax, ax
ret
pc88va_root_lookup_core: mov ax, 99
ret
pc88va_stage2_root_name_pointer: dw 0
pc88va_stage2_config_name: db 'CONFIG  SYS'
pc88va_stage2_kernel_name: db 'KERNEL  SYS'
pc88va_stage2_config_file: times FL_SIZE db 0
pc88va_stage2_file: times FL_SIZE db 0
pc88va_stage2_mz: times MZ_CONTEXT_SIZE db 0
pc88va_stage2_root: times RT_SIZE db 0
'''
        with tempfile.TemporaryDirectory() as tmp:
            asm, binary = Path(tmp) / 'selector.asm', Path(tmp) / 'selector.bin'
            asm.write_text(nasm_definitions(profile['layout']) + source)
            subprocess.run(['nasm', '-f', 'bin', '-I' + str(ROOT / 'components/fdkernel/pc88va/boot') + '/',
                            str(asm), '-o', str(binary)], check=True)
            code = binary.read_bytes()
        entry, value, cfg, file, mz, segment, offset, length, mzseg = struct.unpack_from('<9H', code)
        cases = [(b'FILES=20\r\n', 0), (b'PC88VA_LOADSEG=1000\r\n', 0x1000),
                 (b'PC88VA_LOADSEG=2000h\r\n', 0x2000), (b'PC88VA_LOADSEG=3000\r\n', 0x3000),
                 (b'PC88VA_LOADSEG=0800\r\n', None), (b'PC88VA_LOADSEG=0000\r\n', None),
                 (b'PC88VA_LOADSEG=FFFF\r\n', None), (b'PC88VA_LOADSEG=2000 garbage\r\n', None),
                 (b'PC88VA_LOADSEG=2000\r\nPC88VA_LOADSEG=3000\r\n', None)]
        for config, expected in cases:
            with self.subTest(config=config):
                cpu = Uc(UC_ARCH_X86, UC_MODE_16); cpu.mem_map(0, 0x100000)
                cpu.mem_write(0x10000, code); cpu.mem_write(0x30000, config)
                def word(at, val): cpu.mem_write(0x10000 + at, struct.pack('<H', val))
                word(cfg + segment, 0x3000); word(cfg + offset, 0); word(cfg + length, len(config))
                word(file + segment, 0x2700); word(mz + mzseg, 0x2700)
                cpu.mem_write(0x28000, struct.pack('<H', 0xff00))
                for name, val in dict(CS=0x1000, DS=0x1000, SS=0x2000, SP=0x8000).items():
                    cpu.reg_write(getattr(r, 'UC_X86_REG_' + name), val)
                cpu.emu_start(0x10000 + entry, 0x1ff00, count=10000)
                if expected is None:
                    self.assertNotEqual(cpu.reg_read(r.UC_X86_REG_AX), 0)
                else:
                    self.assertEqual(cpu.reg_read(r.UC_X86_REG_AX), 0)
                    self.assertEqual(struct.unpack('<H', cpu.mem_read(0x10000 + value, 2))[0], expected)
                self.assertEqual(bytes(cpu.mem_read(0x10000 + file + segment, 2)), b'\x00\x27')
                self.assertEqual(bytes(cpu.mem_read(0x10000 + mz + mzseg, 2)), b'\x00\x27')

    def test_stage2_measures_before_first_disk_read(self):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_MEM_READ
        from unicorn import x86_const as r
        from build_loader import build_stage
        profile = json.loads((ROOT / 'config/m19/loader.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = build_stage(profile, out, 2)
            code = (out / 'stage2.bin').read_bytes()
        symbols = result['symbols']
        for capacity in (256, 384, 511, 512, 640):
            with self.subTest(capacity=capacity):
                cpu = Uc(UC_ARCH_X86, UC_MODE_16)
                cpu.mem_map(0, 0x100000)
                cpu.mem_write(0, b'\xa5' * 0x100000)
                cpu.mem_write(0x12000, code)
                def absent(uc, access, address, size, value, data):
                    uc.mem_write(address, b'\xff' * size)
                if capacity < 640:
                    cpu.hook_add(UC_HOOK_MEM_READ, absent, None, capacity * 1024, 0x9ffff)
                reached = []
                def stop(uc, address, size, data):
                    reached.append(address)
                    uc.emu_stop()
                for key in ('adapter', 'failure'):
                    at = 0x12000 + symbols[key]
                    cpu.hook_add(UC_HOOK_CODE, stop, begin=at, end=at)
                cpu.reg_write(r.UC_X86_REG_CS, 0x1200)
                cpu.emu_start(0x12000, 0xfffff, count=100000)
                self.assertEqual(reached, [0x12000 + symbols['adapter']])
                expected = struct.pack('<H', capacity * 64 - 0x1900)
                for key, field in (('file', 10), ('mz', 4), ('mz', 8)):
                    self.assertEqual(bytes(cpu.mem_read(0x12000 + symbols[key] + field, 2)), expected)
