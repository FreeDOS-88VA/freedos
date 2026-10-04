#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""M20-maintained ROM-free linked placement and carrier regressions.

Copied from the integrated M17 suite at M18 START_SHA
`d81bba18f0e4793d7165fb0acfdf7e229e160c83`; this suite uses only M20-local
helpers/configuration and does not carry M17 acceptance state.
"""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('carrier_m20', ROOT / 'tools/m20/build_compressed_kernel.py')
carrier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(carrier)


def fixture(length=1024):
    body = bytearray((i * 7) & 255 for i in range(length))
    struct.pack_into('<H', body, 16, 2)
    stack = (length + 15) // 16
    header = (0x5A4D, 0, 0, 1, 3, 256, 0xFFFF, stack, 4096, 0, 0, 0, 28, 0)
    return header, bytes(body), struct.pack('<HH', 16, 0)


class PlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'build/m20').mkdir(parents=True, exist_ok=True)

    def plan(self, h=None, body=None, rel=None, **kw):
        fh, fb, fr = fixture()
        args = dict(image_segment=0x1000, load_segment=0x6800,
                    file_segment=0x4800, scratch_segment=0x2800, source_extent=8192)
        args.update(kw)
        return carrier.plan_layout(h or fh, fb if body is None else body,
                                   fr if rel is None else rel, **args)

    def test_stack_and_alignment_are_in_live_extent(self):
        for size in (1023, 1024, 1025, 65535, 65536, 65537):
            h, b, r = fixture(size)
            p = self.plan(h, b, r)
            self.assertEqual(p['stack'][1], 0x10000 + ((size + 15) & ~15) + 4096)
            self.assertEqual(p['ranges']['image'][1], p['stack'][1])

    def test_in_place_handoff_frame_does_not_overwrite_relocation_tail(self):
        with tempfile.TemporaryDirectory(prefix='m20-m13-frame-', dir=ROOT / 'build/m20') as tmp:
            tmp = Path(tmp)
            for length in range(32, 64):
                with self.subTest(length=length):
                    h, body, relocations = fixture(length)
                    h = list(h)
                    size = 48 + len(body)
                    h[1], h[2] = size % 512, (size + 511) // 512
                    kernel = tmp / 'fixture.exe'
                    kernel.write_bytes(struct.pack('<14H', *h) + relocations + bytes(16) + body)
                    output = tmp / 'carrier.exe'
                    record = carrier.build(
                        kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm', output,
                        load_segment=0x2600, file_segment=0x2600,
                        scratch_segment=0x3600, source_offset=4096,
                        image_segment=0x1000)
                    live_end = (record['payload_offset'] + record['payload_size'] +
                                record['relocation_count'] * 4)
                    # The in-place bridge has a bounded paragraph-aligned
                    # prefix, without the ordinary carrier's unused padding.
                    self.assertEqual(record['payload_offset'], 0x280)
                    # loader_handoff.inc pushes a four-byte FAR return frame
                    # before the unpacker can copy the relocation records.
                    self.assertGreaterEqual(record['carrier_stack_pointer'] - 4, live_end)
                    allocation = ((len(output.read_bytes()) - 32 + 15) // 16) * 16
                    self.assertLessEqual(record['carrier_stack_pointer'], allocation)

    def test_exact_limit_and_one_byte_short(self):
        p = self.plan()
        end = p['ranges']['bridge'][1]
        # This ceiling must also cover the carrier while it is still live.
        end = max(end, 0x68000 + carrier.MAX_CARRIER_FILE)
        self.plan(memory_top=end)
        with self.assertRaises(ValueError):
            self.plan(memory_top=end - 1)

    def test_reject_live_scratch_and_bridge_overlap(self):
        for target in (0x2800, 0x4800):
            with self.assertRaises(ValueError):
                self.plan(image_segment=target)

    def test_reject_firmware_and_segment_wrap(self):
        for target in (-1, 0xFFF, 0xFFFF, 0x10000):
            with self.assertRaises(ValueError):
                self.plan(image_segment=target)

    def test_reject_stack_alias_and_bad_entry(self):
        h, b, r = fixture()
        for index, value in ((7, 0), (8, 4094), (11, 0x1000)):
            bad = list(h)
            bad[index] = value
            with self.assertRaises(ValueError):
                self.plan(bad, b, r)

    def test_reject_relocation_outside_file_or_wrapped_word(self):
        for record in (struct.pack('<HH', 1023, 0), struct.pack('<HH', 65535, 0)):
            with self.assertRaises(ValueError):
                self.plan(rel=record)
        h, b, r = fixture()
        bad = bytearray(b)
        struct.pack_into('<H', bad, 16, 0xFFFF)
        with self.assertRaises(ValueError):
            self.plan(h, bytes(bad), r)

    def test_reject_carrier_overlapping_copy_destinations(self):
        with self.assertRaises(ValueError):
            self.plan(load_segment=0x2800)
        # Equal file/load segments are the explicit in-place staging mode;
        # this case is valid and is checked by the dedicated execution test.
        plan = self.plan(load_segment=0x4800)
        self.assertTrue(plan['in_place'])

    def split_fixture(self, init_size=48, code=b'\x9a\x02\x00'):
        body = bytearray(128 + init_size)
        body[0:8] = b'M13PLAN1'
        # Enumerated relocation sites: low CALL to HMA, low CALL to INIT,
        # and a CALL within INIT back to HMA. Unlisted lookalikes stay data.
        body[32:35] = code
        struct.pack_into('<H', body, 35, 4)
        body[40:43] = b'\x9a\x01\x00'
        struct.pack_into('<H', body, 43, 8)
        body[128:133] = b'\x9a\x03\x00\x04\x00'
        body[96:101] = b'\x9a\x02\x00\x04\x00'
        rel = b''.join(struct.pack('<HH', off, 0) for off in (35, 43, 131))
        rows = [
            'DATA DATA DGROUP 0000:0000 00000040',
            'HMA_TEXT CODE HMA_GROUP 0004:0000 00000010',
            'CODE CODE CGROUP 0005:0000 00000030',
            'M13_INIT_TEXT M13INIT M13_INIT_GROUP 0008:0000 %08x' % init_size,
            '_STACK STACK DGROUP %04x:0000 00001000' % ((128 + init_size + 15) // 16),
            'Memory Map',
        ]
        return bytes(body), rel, '\n'.join(rows)

    def split_plan(self, body, rel, text, **kwargs):
        with tempfile.TemporaryDirectory(prefix='m20-m13-split-', dir=ROOT / 'build/m20') as tmp:
            path = Path(tmp) / 'fixture.map'
            path.write_text(text)
            return carrier.split_image(body, rel, path, 0x1000, **kwargs)

    def test_split_retargets_only_enumerated_records(self):
        body, rel, text = self.split_fixture()
        changed, plan = self.split_plan(body, rel, text)
        self.assertEqual(plan['resident_text'], [0x10080, 0x10090])
        self.assertEqual(struct.unpack_from('<H', changed, 35)[0], 8)
        self.assertEqual(struct.unpack_from('<H', changed, 131)[0], 8)
        self.assertEqual(struct.unpack_from('<H', changed, 43)[0], plan['init'][0] // 16 - 0x1000)
        self.assertEqual(changed[96:101], body[96:101])
        self.assertEqual(plan['init_stack'][1] - plan['init_stack'][0], 4096)

    def test_split_rounding_and_descriptor(self):
        for size in (31, 32, 33, 255, 256, 257):
            body, rel, text = self.split_fixture(size)
            changed, plan = self.split_plan(body, rel, text)
            rounded = (size + 15) & ~15
            self.assertEqual(plan['init'][0], 0xA0000 - 4096 - rounded)
            self.assertEqual(plan['init'][1] - plan['init'][0], size)
            self.assertEqual(plan['init_stack'][0], 0x9F000)
            self.assertEqual(struct.unpack_from('<8H', changed, 8),
                             (0x1000, 0x1008, plan['init'][0] // 16,
                              size, 0x9F00, 4096, 0xA000, 1))

    def test_split_places_init_at_runtime_top_above_low_staging_at_256k(self):
        body, rel, text = self.split_fixture(256)
        changed, plan = self.split_plan(body, rel, text,
                                        memory_top=0x40000, init_top=0x40000,
                                        runtime_top=True)
        self.assertLessEqual(plan['init_stack'][1], 0x40000)
        self.assertEqual(plan['init_stack'][1], 0x40000)
        self.assertEqual(struct.unpack_from('<H', changed, 8 + 6 * 2)[0], 0)

    def test_split_rejects_unknown_reference_and_stale_descriptor(self):
        body, rel, text = self.split_fixture(code=b'\x90\x90\x90')
        with self.assertRaises(ValueError):
            self.split_plan(body, rel, text)
        body, rel, text = self.split_fixture()
        for offset in (0, 8):
            bad = bytearray(body)
            bad[offset] = 1
            with self.assertRaises(ValueError):
                self.split_plan(bytes(bad), rel, text)
        bad = bytearray(body)
        bad[80:88] = b'M13PLAN1'
        with self.assertRaises(ValueError):
            self.split_plan(bytes(bad), rel, text)

    def test_split_rejects_live_overlap_and_bad_group(self):
        body, rel, text = self.split_fixture()
        with self.assertRaises(ValueError):
            self.split_plan(body, rel, text, memory_top=0x110A0)
        with self.assertRaises(ValueError):
            self.split_plan(body, rel, text.replace('M13_INIT_GROUP', 'CGROUP'))

    def test_execute_real_bridge_at_low_destination(self):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_DX
        for size in (4096, 65553):
            h, b, r = fixture(size)
            h = list(h)
            file_size = 48 + len(b)
            h[1], h[2] = file_size % 512, (file_size + 511) // 512
            with tempfile.TemporaryDirectory(prefix='m20-m13-placement-', dir=ROOT / 'build/m20') as tmp:
                tmp = Path(tmp)
                kernel = tmp / 'fixture.exe'
                kernel.write_bytes(struct.pack('<14H', *h) + r + bytes(16) + b)
                output = tmp / 'carrier.exe'
                record = carrier.build(kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm', output,
                                       load_segment=0x6800, file_segment=0x4800,
                                       scratch_segment=0x2800, source_offset=4096)
                uc = Uc(UC_ARCH_X86, UC_MODE_16)
                uc.mem_map(0, 0x100000)
                uc.mem_write(0, bytes([0xA5]) * 0x100000)
                uc.mem_write(0x68000, output.read_bytes()[32:])
                uc.reg_write(UC_X86_REG_CS, 0x6800)
                uc.reg_write(UC_X86_REG_IP, 0)
                uc.reg_write(UC_X86_REG_SS, 0x6800)
                uc.reg_write(UC_X86_REG_SP, 1024)
                uc.reg_write(UC_X86_REG_DX, 0x1234)
                reached = []
                def stop(cpu, address, length, data):
                    reached.append(address)
                    cpu.emu_stop()
                uc.hook_add(UC_HOOK_CODE, stop, begin=0x10000, end=0x10000)
                uc.emu_start(0x68000, 0xFFFFF, timeout=10000000, count=3000000)
                self.assertEqual(reached, [0x10000])
                expected = bytearray(b)
                struct.pack_into('<H', expected, 16, 0x1002)
                self.assertEqual(bytes(uc.mem_read(0x10000, len(b))), bytes(expected))
                self.assertEqual(uc.reg_read(UC_X86_REG_SS), 0x1000 + h[7])
                self.assertEqual(uc.reg_read(UC_X86_REG_SP), 4096)
                self.assertEqual(uc.reg_read(UC_X86_REG_DX), 0x1234)
                self.assertEqual(uc.mem_read(0xFFFF, 1), bytes([0xA5]))
                # The final trampoline legitimately used the stack's top four bytes.
                zero_length = record['layout']['zero_bytes'] - 4
                self.assertEqual(bytes(uc.mem_read(0x10000 + len(b), zero_length)), bytes(zero_length))
                self.assertEqual(uc.mem_read(record['layout']['ranges']['image'][1], 1), bytes([0xA5]))

    def test_execute_in_place_low_staging_bridge_under_256k(self):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_DX
        h, b, r = fixture(4096)
        h = list(h)
        file_size = 48 + len(b)
        h[1], h[2] = file_size % 512, (file_size + 511) // 512
        with tempfile.TemporaryDirectory(prefix='m20-m13-in-place-', dir=ROOT / 'build/m20') as tmp:
            tmp = Path(tmp)
            kernel = tmp / 'fixture.exe'
            kernel.write_bytes(struct.pack('<14H', *h) + r + bytes(16) + b)
            output = tmp / 'carrier.exe'
            record = carrier.build(kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm', output,
                                   load_segment=0x2600, file_segment=0x2600,
                                   scratch_segment=0x3600, source_offset=4096,
                                   image_segment=0x1000)
            self.assertTrue(record['layout']['in_place'])
            carrier_header = struct.unpack_from('<14H', output.read_bytes())
            carrier_allocation = ((len(output.read_bytes()) - 32 + 15) // 16) * 16
            self.assertEqual(record['carrier_allocation'], carrier_allocation)
            self.assertEqual(record['carrier_stack_pointer'], carrier_allocation)
            self.assertEqual(carrier_header[7:9], (0, carrier_allocation))
            self.assertGreater(carrier_header[8], 1024)
            self.assertLessEqual(carrier_header[8] + 4, 0xEF00)
            self.assertLess(record['layout']['ranges']['bridge'][1], 0x40000 + 1)
            uc = Uc(UC_ARCH_X86, UC_MODE_16)
            uc.mem_map(0, 0x100000)
            uc.mem_write(0, bytes([0xA5]) * 0x100000)
            # The real MZ handoff has already compacted the body to offset 0.
            uc.mem_write(0x26000, output.read_bytes()[32:])
            uc.reg_write(UC_X86_REG_CS, 0x2600)
            uc.reg_write(UC_X86_REG_IP, 0)
            uc.reg_write(UC_X86_REG_SS, 0x2600)
            uc.reg_write(UC_X86_REG_SP, 1024)
            uc.reg_write(UC_X86_REG_DX, 0x4321)
            reached = []
            def stop(cpu, address, length, data):
                reached.append(address)
                cpu.emu_stop()
            uc.hook_add(UC_HOOK_CODE, stop, begin=0x10000, end=0x10000)
            uc.emu_start(0x26000, 0xFFFFF, timeout=10000000, count=3000000)
            self.assertEqual(reached, [0x10000])
            expected = bytearray(b)
            struct.pack_into('<H', expected, 16, 0x1002)
            self.assertEqual(bytes(uc.mem_read(0x10000, len(b))), bytes(expected))
            self.assertEqual(uc.reg_read(UC_X86_REG_SS), 0x1000 + h[7])
            self.assertEqual(uc.reg_read(UC_X86_REG_SP), 4096)
            self.assertEqual(uc.reg_read(UC_X86_REG_DX), 0x4321)

    def test_low_staging_envelope_fits_every_supported_capacity(self):
        h, b, r = fixture(4096)
        for memory_top in (0x40000, 0x60000, 0x80000, 0xA0000):
            plan = self.plan(h, b, r, load_segment=0x2600,
                             file_segment=0x2600, scratch_segment=0x3600,
                             memory_top=memory_top)
            self.assertTrue(plan['in_place'])
            for start, end in plan['ranges'].values():
                self.assertLessEqual(end, memory_top)

    def test_va_fixed_loader_profile_is_source_bound(self):
        profile_path = ROOT / 'config/m20/va-fixed-loader-profile-test.json'
        profile = json.loads(profile_path.read_text())
        loader_tools = ROOT / 'tools/m20'
        profile_spec = importlib.util.spec_from_file_location(
            'm13_loader_profile', loader_tools / 'loader_profile.py')
        profile_module = importlib.util.module_from_spec(profile_spec)
        profile_spec.loader.exec_module(profile_module)
        loader = importlib.util.spec_from_file_location(
            'm13_build_loader', loader_tools / 'build_loader.py')
        loader_module = importlib.util.module_from_spec(loader)
        import sys
        sys.modules['loader_profile'] = profile_module
        loader.loader.exec_module(loader_module)

        self.assertEqual(loader_module.validate_overlay(profile), profile)
        definitions = profile_module.definitions(profile['layout'])
        self.assertEqual(profile['bootstrap']['image_segment'], 0x3000)
        self.assertEqual(definitions['PC88VA_INITIAL_LOAD_SEGMENT'], 0x1340)
        self.assertEqual(definitions['PC88VA_LOW_STAGING_SEGMENT'], 0x1340)
        self.assertEqual(definitions['S2_KERNEL_ALLOCATION_SEGMENT'], 0x3000)
        self.assertEqual(definitions['S2_KERNEL_IN_PLACE'], 0)
        regions = profile['layout']['regions']
        self.assertEqual(regions['kernel_file'], [0x13400, 0x22ff0])
        self.assertEqual(regions['kernel_allocation'], [0x30000, 0x3fff0])
        self.assertLessEqual(regions['kernel_file'][1] -
                             regions['kernel_file'][0], 0x10000)
        self.assertEqual(profile['layout']['stack']['segment'], 0x77ff)

    def test_low_staging_carrier_builds_at_every_supported_capacity(self):
        h, b, r = fixture(4096)
        h = list(h)
        file_size = 48 + len(b)
        h[1], h[2] = file_size % 512, (file_size + 511) // 512
        with tempfile.TemporaryDirectory(prefix='m20-m13-low-capacities-', dir=ROOT / 'build/m20') as tmp:
            tmp = Path(tmp)
            kernel = tmp / 'fixture.exe'
            kernel.write_bytes(struct.pack('<14H', *h) + r + bytes(16) + b)
            for memory_top in (0x40000, 0x60000, 0x80000, 0xA0000):
                output = tmp / ('carrier-%x.exe' % memory_top)
                record = carrier.build(kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm',
                                       output, load_segment=0x2600, file_segment=0x2600,
                                       scratch_segment=0x3600, source_offset=4096,
                                       image_segment=0x1000, memory_top=memory_top)
                self.assertTrue(record['layout']['in_place'])
                self.assertTrue(all(end <= memory_top for start, end in record['layout']['ranges'].values()))
                self.assertLessEqual(record['carrier_stack_pointer'], 0xEF40)

    def test_low_staging_split_init_stays_below_fixed_carrier(self):
        body, rel, text = self.split_fixture(256)
        h = (0x5A4D, 0, 0, len(rel) // 4, 3, 256, 0xFFFF, 32,
             4096, 0, 0, 0, 28, 0)
        file_size = 48 + len(body)
        h = list(h)
        h[1], h[2] = file_size % 512, (file_size + 511) // 512
        with tempfile.TemporaryDirectory(prefix='m20-m13-low-split-', dir=ROOT / 'build/m20') as tmp:
            tmp = Path(tmp)
            kernel = tmp / 'fixture.exe'
            kernel.write_bytes(struct.pack('<14H', *h) + rel + bytes(8) + body)
            link_map = tmp / 'fixture.map'
            link_map.write_text(text)
            output = tmp / 'carrier.exe'
            record = carrier.build(kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm',
                                   output, load_segment=0x2600,
                                   file_segment=0x2600, scratch_segment=0x3600,
                                   source_offset=4096, image_segment=0x1000,
                                   link_map=link_map, memory_top=0x40000)
            self.assertLessEqual(record['split']['init_stack'][1], 0x40000)
            self.assertGreaterEqual(record['split']['init'][0], 0x26000)

    def test_split_init_is_safe_for_runtime_512k_with_640k_build_default(self):
        body, rel, text = self.split_fixture(256)
        h = (0x5A4D, 0, 0, len(rel) // 4, 3, 256, 0xFFFF, 32,
             4096, 0, 0, 0, 28, 0)
        file_size = 48 + len(body)
        h = list(h)
        h[1], h[2] = file_size % 512, (file_size + 511) // 512
        with tempfile.TemporaryDirectory(prefix='m20-m13-runtime-top-', dir=ROOT / 'build/m20') as tmp:
            tmp = Path(tmp)
            kernel = tmp / 'fixture.exe'
            kernel.write_bytes(struct.pack('<14H', *h) + rel + bytes(8) + body)
            link_map = tmp / 'fixture.map'
            link_map.write_text(text)
            output = tmp / 'carrier.exe'
            record = carrier.build(
                kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm',
                output, load_segment=0x3000, file_segment=0x1340,
                scratch_segment=0x4000, source_offset=4096,
                image_segment=0x1000, link_map=link_map,
                memory_top=0xA0000, bridge_in_allocation=True)
            staging_end = max(0x1340 * 16 + carrier.MAX_CARRIER_FILE,
                              0x3000 * 16 + carrier.MAX_CARRIER_FILE,
                              0x4000 * 16 + carrier.MAX_CARRIER_FILE)
            self.assertEqual(record['memory_top'], 0xA0000)
            self.assertEqual(record['minimum_runtime_memory_kb'], 384)
            self.assertEqual(record['definitions']['M13_RUNTIME_MEMORY_TOP'], 1)
            self.assertEqual(record['split']['init_stack'][1], record['init_top'])
            self.assertGreaterEqual(record['split']['init'][0], staging_end)
            self.assertLessEqual(record['init_top'], 0x80000)

            # The same linked image and carrier bytes remain valid at either
            # supported capacity above this split profile's fixed early ranges.
            record_384 = carrier.build(
                kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm',
                tmp / 'carrier-384.exe', load_segment=0x3000,
                file_segment=0x1340, scratch_segment=0x4000,
                source_offset=4096, image_segment=0x1000, link_map=link_map,
                memory_top=0x60000,
                bridge_in_allocation=True)
            self.assertEqual(record_384['minimum_runtime_memory_kb'], 384)
            self.assertEqual(record_384['init_top'], record['init_top'])
            self.assertEqual(record_384['split']['init_stack'][1], record['init_top'])
            self.assertEqual(output.read_bytes(), (tmp / 'carrier-384.exe').read_bytes())

    def test_low_in_place_split_layout_fits_256_with_640_build_default(self):
        body, rel, text = self.split_fixture(256)
        h = (0x5A4D, 0, 0, len(rel) // 4, 3, 256, 0xFFFF, 32,
             4096, 0, 0, 0, 28, 0)
        file_size = 48 + len(body)
        h = list(h)
        h[1], h[2] = file_size % 512, (file_size + 511) // 512
        with tempfile.TemporaryDirectory(prefix='m20-m13-runtime-256-', dir=ROOT / 'build/m20') as tmp:
            tmp = Path(tmp)
            kernel = tmp / 'fixture.exe'
            kernel.write_bytes(struct.pack('<14H', *h) + rel + bytes(8) + body)
            link_map = tmp / 'fixture.map'
            link_map.write_text(text)
            output_640 = tmp / 'carrier-640.exe'
            profile = dict(
                load_segment=0x2700, file_segment=0x2700, scratch_segment=0x3700,
                source_offset=4096, image_segment=0x1000, link_map=link_map,
                bridge_in_allocation=False)
            record_640 = carrier.build(
                kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm',
                output_640, memory_top=0xA0000, **profile)
            output_256 = tmp / 'carrier-256.exe'
            record_256 = carrier.build(
                kernel, ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm',
                output_256, memory_top=0x40000, **profile)

            self.assertEqual(record_640['minimum_runtime_memory_kb'], 256)
            self.assertEqual(record_640['definitions']['M13_RUNTIME_MEMORY_TOP'], 1)
            self.assertLessEqual(record_640['minimum_runtime_memory_top'], 0x40000)
            self.assertLessEqual(record_640['split']['init_stack'][1], 0x40000)
            self.assertLessEqual(record_640['init_top'], 0x40000)
            self.assertEqual(record_256['init_top'], record_640['init_top'])
            self.assertEqual(output_256.read_bytes(), output_640.read_bytes())

    def test_measured_capacity_samples_restore_bytes_and_ignore_saved_selection(self):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_MEM_READ, UC_HOOK_INSN
        from unicorn import x86_const as r
        source = (ROOT / 'components/fdkernel/pc88va/kernel/m13_platform.asm').read_text()
        routine = source.split('PC88VA_MEMORY_KB:\n', 1)[1].split('; Return the segment', 1)[0]
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/m20') as tmp:
            asm, binary = Path(tmp) / 'probe.asm', Path(tmp) / 'probe.bin'
            asm.write_text('bits 16\ncpu 8086\n%include "m16_memory_probe.inc"\n' + routine)
            subprocess.run(['nasm', '-f', 'bin', '-I' + str(ROOT / 'components/fdkernel/pc88va/kernel') + '/',
                            str(asm), '-o', str(binary)], check=True)
            code = binary.read_bytes()
        samples = [256 * 1024 - 1] + [n * 1024 for n in range(256, 640)]
        for physical in (128, 256, 384, 511, 512, 640):
            for saved in (0, 1, 3, 4, 7):
                for bus in (0, 255):
                    with self.subTest(physical=physical, saved=saved, bus=bus):
                        cpu = Uc(UC_ARCH_X86, UC_MODE_16)
                        cpu.mem_map(0, 0x100000)
                        cpu.mem_write(0x10000, code)
                        cpu.mem_write(0x21000, struct.pack('<HH', 0x800, 0x1000))
                        cpu.mem_write(0xb1fc4, bytes([0x60 | saved]))
                        original = {address: bytes([(index * 37) & 255 if address < physical * 1024 else bus])
                                    for index, address in enumerate(samples)}
                        for address, value in original.items():
                            cpu.mem_write(address, value)
                        reads = set()
                        def read(uc, access, address, size, value, _):
                            self.assertIn(address, original)
                            self.assertEqual(size, 1)
                            reads.add(address)
                            if address >= physical * 1024:
                                uc.mem_write(address, bytes([bus]))
                        def no_port(*_):
                            self.fail('RAM measurement changed or read a bank port')
                        cpu.hook_add(UC_HOOK_MEM_READ, read, None, samples[0], samples[-1])
                        cpu.hook_add(UC_HOOK_INSN, no_port, None, 1, 0, r.UC_X86_INS_IN)
                        cpu.hook_add(UC_HOOK_INSN, no_port, None, 1, 0, r.UC_X86_INS_OUT)
                        preserved = dict(BX=0x5566, CX=0x3344, DX=0x7788, SI=0x1234,
                                         DI=0x8899, BP=0x1122, DS=0x3456, ES=0x4567)
                        for name, value in dict(preserved, CS=0x1000, SS=0x2000, SP=0x1000,
                                               EFLAGS=0x602).items():
                            cpu.reg_write(getattr(r, 'UC_X86_REG_' + name), value)
                        cpu.emu_start(0x10000, 0x10800, count=20000)
                        self.assertEqual(cpu.reg_read(r.UC_X86_REG_AX), physical if physical >= 256 else 0)
                        self.assertEqual(cpu.reg_read(r.UC_X86_REG_SP), 0x1004)
                        for name, value in preserved.items():
                            self.assertEqual(cpu.reg_read(getattr(r, 'UC_X86_REG_' + name)), value)
                        self.assertEqual(cpu.reg_read(r.UC_X86_REG_EFLAGS) & 0x600, 0x600)
                        expected = {samples[0]}
                        if physical >= 256:
                            expected.update(n * 1024 for n in range(256, min(physical + 1, 640)))
                        self.assertEqual(reads, expected)
                        for address, value in original.items():
                            self.assertEqual(bytes(cpu.mem_read(address, 1)), value)

    def test_reset_actual_far_entry_and_register_contract(self):
        """Assemble the production entry, not a replacement implementation."""
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
        from unicorn import x86_const as regs
        source = (ROOT / 'components/fdkernel/pc88va/kernel/m13_platform.asm').read_text()
        entry = source.split('FL_RESET:\n', 1)[1].split('global FL_DISKCHANGED', 1)[0]
        with tempfile.TemporaryDirectory(prefix='m20-m13-reset-', dir=ROOT / 'build/m20') as tmp:
            tmp = Path(tmp)
            asm = tmp / 'reset.asm'
            asm.write_text('bits 16\ncpu 8086\n' + entry)
            binary = tmp / 'reset.bin'
            subprocess.run(['nasm', '-f', 'bin', str(asm), '-o', str(binary)], check=True)
            for drive in (0, 1, 0xFFFF):
                cpu = Uc(UC_ARCH_X86, UC_MODE_16)
                cpu.mem_map(0, 0x100000)
                # MOV AX,drive / PUSH AX / CALL FAR / caller continuation.
                caller = b'\xb8' + struct.pack('<H', drive) + b'\x50\x9a\x00\x00\x00\x20'
                cpu.mem_write(0x10000, caller)
                cpu.mem_write(0x20000, binary.read_bytes())
                values = dict(CS=0x1000, SS=0x3000, SP=0x800,
                              BX=0x1234, CX=0x2345, DX=0x3456, SI=0x4567,
                              DI=0x5678, BP=0x6789, DS=0x4000, ES=0x5000)
                for name, value in values.items():
                    cpu.reg_write(getattr(regs, 'UC_X86_REG_' + name), value)
                # M14 implements a native reset call; provide only its synthetic
                # firmware boundary instead of assuming the former no-op body.
                calls = []
                failed = drive != 0

                def firmware(machine, interrupt, _):
                    self.assertEqual(interrupt, 0x80)
                    self.assertEqual(machine.reg_read(regs.UC_X86_REG_AX) >> 8, 0)
                    calls.append(interrupt)
                    machine.reg_write(regs.UC_X86_REG_AX, 0)
                    flags = machine.reg_read(regs.UC_X86_REG_EFLAGS)
                    machine.reg_write(regs.UC_X86_REG_EFLAGS, (flags & ~1) | int(failed))

                cpu.hook_add(UC_HOOK_INTR, firmware)
                cpu.emu_start(0x10000, 0x10000 + len(caller), count=32)
                self.assertEqual(calls, [0x80])
                self.assertEqual(cpu.reg_read(regs.UC_X86_REG_AX), int(not failed))
                self.assertEqual(cpu.reg_read(regs.UC_X86_REG_IP), len(caller))
                for name, value in values.items():
                    self.assertEqual(cpu.reg_read(getattr(regs, 'UC_X86_REG_' + name)), value, name)


if __name__ == '__main__':
    (ROOT / 'build/m20').mkdir(parents=True, exist_ok=True)
    unittest.main()
