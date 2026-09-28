#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""M16-maintained execution checks for the owned M13 carrier tail."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('carrier_m16', ROOT / 'tools/m16/build_compressed_kernel.py')
CARRIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CARRIER)
BRIDGE = ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm'


class CarrierTailTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.body = bytearray(bytes(range(256)) * 257)
        struct.pack_into('<H', self.body, 16, 2)
        size = 48 + len(self.body)
        self.stack = (len(self.body) + 15) // 16
        self.header = (0x5A4D, size % 512, (size + 511) // 512, 1, 3,
                       256, 0xFFFF, self.stack, 4096, 0, 0, 0, 28, 0)
        self.kernel = self.root / 'fixture.exe'
        self.kernel.write_bytes(struct.pack('<14H', *self.header)
                                + struct.pack('<HH', 16, 0) + bytes(16) + self.body)
        self.output = self.root / 'carrier.exe'

    def build(self, **overrides):
        args = dict(load_segment=0x3000, file_segment=0x3000,
                    scratch_segment=0x2800, source_offset=4096,
                    memory_top=0x80000)
        args.update(overrides)
        return CARRIER.build(self.kernel, BRIDGE, self.output, **args)

    def test_explicit_historical_offset_preserves_exact_bytes(self):
        old = self.build()
        data = self.output.read_bytes()
        explicit = self.build(ring_offset=0xEF40)
        self.assertEqual(data, self.output.read_bytes())
        self.assertEqual(old, explicit)

    def test_reject_unaligned_external_or_wrong_mode_ring(self):
        for offset in (-16, 0xEFF1, 0xF000, 0x10000, True):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.build(ring_offset=offset)
        with self.assertRaises(ValueError):
            self.build(load_segment=0x5000, ring_offset=0xEFF0)
        with self.assertRaisesRegex(ValueError, 'no room'):
            self.build(ring_offset=0x280)

    def test_execute_at_last_owned_byte_with_outside_guards(self):
        self.execute_with_guards(False)

    def test_compact_bridge_preserves_decoder_relocations_stack_and_bounds(self):
        original = self.build(ring_offset=0xEFF0)
        compact = self.build(ring_offset=0xEFF0, compact_bridge=True)
        self.assertLess(compact['bridge_size'], original['bridge_size'])
        self.assertEqual(compact['payload_offset'], compact['bridge_size'])
        self.assertEqual(original['payload_offset'], 0x280)
        self.assertLess(compact['size'], original['size'])
        self.assertEqual(compact['payload_size'], original['payload_size'])
        self.assertEqual(compact['layout'], original['layout'])
        with self.assertRaises(ValueError):
            self.build(load_segment=0x5000, compact_bridge=True)
        self.execute_with_guards(True)

    def test_external_history_ring_preserves_carrier_and_expands_exact_bytes(self):
        record = self.build(load_segment=0x2700, file_segment=0x2700,
                            scratch_segment=0x3700, ring_segment=0x3800,
                            ring_offset=0, memory_top=0x40000)
        self.assertEqual(record['layout']['ranges']['ring'], (0x38000, 0x39000))
        self.assertEqual(record['layout']['ranges']['bridge_stack'],
                         (0x3eff0, 0x3fff0))
        self.assertEqual(record['definitions']['M13_RING_SEG'], 0x3800)
        original_carrier = self.output.read_bytes()
        cpu, reg = self.new_machine()
        carrier_base = 0x27000
        cpu.mem_write(carrier_base, original_carrier[32:])
        for name, value in dict(CS=0x2700, IP=0, SS=0x2700,
                                SP=record['carrier_stack_pointer'], DX=0x4321).items():
            cpu.reg_write(getattr(reg, 'UC_X86_REG_' + name), value)
        reached = []
        def stop(machine, address, length, data):
            reached.append(address)
            machine.emu_stop()
        from unicorn import UC_HOOK_CODE
        cpu.hook_add(UC_HOOK_CODE, stop, begin=0x10000, end=0x10000)
        cpu.emu_start(carrier_base, 0xfffff, timeout=10000000, count=3000000)
        self.assertEqual(reached, [0x10000])
        expected = bytearray(self.body)
        struct.pack_into('<H', expected, 16, 0x1002)
        self.assertEqual(bytes(cpu.mem_read(0x10000, len(expected))), bytes(expected))
        source_start = record['payload_offset']
        source_end = source_start + record['payload_size'] + record['relocation_count'] * 4
        self.assertEqual(bytes(cpu.mem_read(carrier_base + source_start,
                                            source_end - source_start)),
                         original_carrier[32 + source_start:32 + source_end])
        self.assertNotEqual(bytes(cpu.mem_read(0x38000, 4096)), b'\xA5' * 4096)

    @staticmethod
    def new_machine():
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
        from unicorn import x86_const as reg
        cpu = Uc(UC_ARCH_X86, UC_MODE_16)
        cpu.mem_map(0, 0x100000)
        cpu.mem_write(0, b'\xA5' * 0x100000)
        return cpu, reg

    def execute_with_guards(self, compact):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
        from unicorn import x86_const as reg
        record = self.build(ring_offset=0xEFF0, compact_bridge=compact)
        self.assertEqual(record['definitions']['M13_RING_OFFSET'] + 4096,
                         CARRIER.MAX_CARRIER_FILE)
        frame_start = record['carrier_stack_pointer'] - 4
        body_end = record['size'] - 32
        self.assertGreaterEqual(frame_start, body_end)
        self.assertLessEqual(record['carrier_stack_pointer'], 0xEFF0)
        cpu = Uc(UC_ARCH_X86, UC_MODE_16)
        cpu.mem_map(0, 0x100000)
        cpu.mem_write(0, b'\xA5' * 0x100000)
        cpu.mem_write(0x30000, self.output.read_bytes()[32:])
        frame = b'\x31\x42\x53\x64'
        cpu.mem_write(0x30000 + frame_start, frame)
        for name, value in dict(CS=0x3000, IP=0, SS=0x3000,
                                SP=record['carrier_stack_pointer'], DX=0x4321).items():
            cpu.reg_write(getattr(reg, 'UC_X86_REG_' + name), value)
        reached = []
        def stop(machine, address, length, data):
            reached.append(address)
            machine.emu_stop()
        cpu.hook_add(UC_HOOK_CODE, stop, begin=0x10000, end=0x10000)
        cpu.emu_start(0x30000, 0xFFFFF, timeout=10000000, count=3000000)
        self.assertEqual(reached, [0x10000])
        expected = bytearray(self.body)
        struct.pack_into('<H', expected, 16, 0x1002)
        self.assertEqual(cpu.mem_read(0x10000, len(expected)), expected)
        self.assertEqual(cpu.mem_read(0x30000 + CARRIER.MAX_CARRIER_FILE, 16), b'\xA5' * 16)
        self.assertEqual(cpu.mem_read(0x30000 + frame_start, 4), frame)
        self.assertEqual(cpu.mem_read(0xFFFF, 1), b'\xA5')
        self.assertEqual(cpu.reg_read(reg.UC_X86_REG_SS), 0x1000 + self.stack)
        self.assertEqual(cpu.reg_read(reg.UC_X86_REG_SP), 4096)
        self.assertEqual(cpu.reg_read(reg.UC_X86_REG_DX), 0x4321)


if __name__ == '__main__':
    unittest.main()
