# SPDX-License-Identifier: GPL-2.0-or-later
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m18/qa'))
from mixed_floppy_360 import prepare, inspect, d88_profile, CONFIG
from tools.m18.media import build_d88, inspect as inspect_d88


class MixedFloppyTests(unittest.TestCase):
    SPEC = json.loads(CONFIG.read_text())

    def test_empty_profile_and_independent_readback(self):
        media = prepare(self.SPEC)
        self.assertEqual(len(media), 368640)
        self.assertEqual(inspect(media, self.SPEC), {})
        wrapped = build_d88(d88_profile(self.SPEC), media)
        self.assertEqual(len(wrapped), 688 + 720 * (16 + 512))
        _, independent = inspect_d88(wrapped, d88_profile(self.SPEC))
        self.assertEqual(independent, {})

    def test_guest_style_file_chain_and_negative_cases(self):
        raw = bytearray(prepare(self.SPEC))
        raw[2560+32:2560+43] = b'MIX     ASM'
        raw[2560+32+11] = 0x20
        raw[2560+32+26:2560+32+28] = (2).to_bytes(2, 'little')
        raw[2560+32+28:2560+32+32] = (4).to_bytes(4, 'little')
        raw[12*512:12*512+4] = b'TEST'
        for offset in (512, 1536):
            raw[offset+3:offset+5] = b'\xff\x0f'  # FAT12 cluster 2 = 0xFFF
        self.assertEqual(inspect(bytes(raw), self.SPEC), {'MIX.ASM': b'TEST'})
        _, independent = inspect_d88(build_d88(d88_profile(self.SPEC), bytes(raw)),
                                     d88_profile(self.SPEC))
        self.assertEqual(independent, {'MIX.ASM': b'TEST'})
        for position, byte, error in (
            (1536, 0, 'FAT copies'),
            (2560+32+26, 0, 'outside data area'),
            (510, 0, 'boot sector'),
            (11, 1, 'BPB'),
        ):
            corrupt = bytearray(raw)
            corrupt[position] = byte
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                inspect(bytes(corrupt), self.SPEC)
        with self.assertRaisesRegex(ValueError, 'length'):
            inspect(bytes(raw[:-1]), self.SPEC)

    def test_profile_is_explicit_not_a_second_distribution(self):
        invalid = dict(self.SPEC, geometry=dict(self.SPEC['geometry'], total_sectors=1280))
        with self.assertRaisesRegex(ValueError, 'accepted public'):
            prepare(invalid)


if __name__ == '__main__':
    unittest.main()
