# SPDX-License-Identifier: GPL-2.0-or-later
import struct
from pathlib import Path
import tempfile
import unittest

from tools.m19.memmap import build_memmap


class MemmapBuilderTests(unittest.TestCase):
    def make_mz(self, directory):
        executable = Path(directory) / "MEMMAP.EXE"
        data = bytearray(64)
        struct.pack_into(
            "<14H", data, 0,
            0x5a4d, 64, 1, 0, 2, 256, 0xffff, 0, 4096, 0, 0, 0, 28, 0,
        )
        executable.write_bytes(data)
        map_file = Path(directory) / "MEMMAP.MAP"
        map_file.write_text(
            "Stack size: 1000 (4096.)\nMemory size: 20 (32.)\n",
            encoding="ascii",
        )
        return executable, map_file, bytes(data)

    def test_maximum_allocation_is_bounded_to_mz_minimum(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable, map_file, original = self.make_mz(temporary)
            self.assertEqual(build_memmap.bound_maximum_allocation(executable), 256)
            result = executable.read_bytes()
            self.assertEqual(result[:12], original[:12])
            self.assertEqual(result[14:], original[14:])
            self.assertEqual(struct.unpack_from("<H", result, 12)[0], 256)
            record = build_memmap.parse_mz(executable, map_file)
            self.assertEqual(record["mz_minimum_extra_paragraphs"], 256)
            self.assertEqual(record["mz_maximum_extra_paragraphs"], 256)
            self.assertEqual(record["required_psp_block_paragraphs"], 274)
            self.assertEqual(record["pinned_freedos_initial_psp_block_paragraphs"], 302)
            self.assertEqual(record["pinned_freedos_page_rounding_overhead_bytes"], 448)

    def test_full_final_page_has_no_extra_page_rounding_cost(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable, map_file, original = self.make_mz(temporary)
            data = bytearray(original.ljust(512, b'\0'))
            struct.pack_into('<H', data, 2, 0)
            executable.write_bytes(data)
            build_memmap.bound_maximum_allocation(executable)
            record = build_memmap.parse_mz(executable, map_file)
            self.assertEqual(record['required_psp_block_paragraphs'], 302)
            self.assertEqual(record['pinned_freedos_initial_psp_block_paragraphs'], 302)
            self.assertEqual(record['pinned_freedos_page_rounding_overhead_bytes'], 0)

    def test_unbounded_mz_is_rejected_before_launch_policy_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable, map_file, _ = self.make_mz(temporary)
            with self.assertRaisesRegex(ValueError, "maximum allocation"):
                build_memmap.parse_mz(executable, map_file)

    def test_maximum_allocation_patcher_rejects_non_mz_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "bad.exe"
            executable.write_bytes(b"not an MZ executable")
            with self.assertRaisesRegex(ValueError, "complete MZ"):
                build_memmap.bound_maximum_allocation(executable)


if __name__ == "__main__":
    unittest.main()
