#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the actual M16 boot-media and first-stage builders per profile."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m16'))
from build_boot_media import BootMediaError, build, profile_inputs
from media import inspect


class BootProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ROOT / 'config/m16/boot-profiles.json').read_text())['profiles']
        cls.media = json.loads((ROOT / 'config/m16/media.json').read_text())
        cls.loader = json.loads((ROOT / 'config/m16/loader.json').read_text())
        cls.payloads = {
            'KERNEL.SYS': b'MZ' + bytes(510),
            'COMMAND.COM': b'COM',
            'COUNTRY.SYS': b'COUNTRY',
            'SYSVA.EXE': b'VA',
        }

    def test_documented_capacities_and_sector_sizes_match_geometry(self):
        expected = {
            '2d-320': (320, 512), '2d-360': (360, 512),
            '2dd-640': (640, 512), '2dd-720': (720, 512),
            '2hd-1232': (1232, 1024), '2hd-1280': (1280, 1024),
        }
        self.assertEqual({p['name'] for p in self.profiles}, set(expected))
        for profile in self.profiles:
            with self.subTest(profile=profile['name']):
                spec, overlay = profile_inputs(profile, self.media, self.loader)
                self.assertEqual(profile['capacity_kib'], expected[profile['name']][0])
                self.assertEqual(spec['geometry']['bytes_per_sector'], expected[profile['name']][1])
                self.assertEqual(overlay['bootstrap']['loaded_bytes'], expected[profile['name']][1])
                expected_code = 2 if expected[profile['name']][1] == 512 else 3
                self.assertIn(f'mov dl, {expected_code}', overlay['firmware_callback'])
                self.assertEqual(spec['geometry']['total_bytes'], profile['capacity_kib'] * 1024)

    def test_2hc_remains_a_data_profile_without_a_boot_profile(self):
        boot_names = {p['name'] for p in self.profiles}
        data_config = json.loads((ROOT / 'config/m16/floppy-profiles.json').read_text())
        data_names = {p['name'] for p in data_config['profiles']}
        self.assertNotIn('2hc-1200', boot_names)
        self.assertIn('2hc-1200', data_names)

    def test_all_first_stages_fit_the_rom_loaded_boot_sector_and_readback(self):
        with tempfile.TemporaryDirectory(prefix='m16-boot-profiles-') as directory:
            root = Path(directory)
            for profile in self.profiles:
                with self.subTest(profile=profile['name']):
                    target = root / profile['name']
                    image, spec, overlay = build(self.payloads, profile, self.media,
                                                 self.loader, target, 1787814827)
                    _, recovered = inspect(image, spec)
                    self.assertEqual(recovered, self.payloads | {
                        'LOADER.BIN': (target / 'loader/stage2.bin').read_bytes()})
                    self.assertEqual((target / 'stage1/stage1.bin').stat().st_size,
                                     overlay['bootstrap']['loaded_bytes'])
                    self.assertEqual(len(image), spec['d88']['declared_size'])

    def test_profile_capacity_drift_is_rejected(self):
        profile = copy.deepcopy(self.profiles[0])
        profile['capacity_kib'] += 1
        with self.assertRaises(BootMediaError):
            profile_inputs(profile, self.media, self.loader)


if __name__ == '__main__':
    unittest.main()
