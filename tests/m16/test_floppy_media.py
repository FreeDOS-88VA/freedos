#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""ROM-free tests for M16 FAT12/D88 media profiles and readback."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'm16_floppy_media', ROOT / 'tools/m16/build_floppy_media.py')
MEDIA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEDIA)


class FloppyMediaTests(unittest.TestCase):
    def test_multicluster_payload_crosses_tracks_without_overlap(self):
        source = json.loads((ROOT / 'config/m16/floppy-profiles.json').read_text())
        payload = bytes((i * 37 + i // 251) & 255 for i in range(32771))
        for profile in source['profiles']:
            with self.subTest(profile=profile['name']):
                spec = MEDIA.profile_spec(profile, source, 1787814827)
                image, report = MEDIA.build_volume(
                    spec, 'PATTERN.BIN', payload, 1787814827)
                _, files = MEDIA.inspect(image, spec)
                self.assertEqual(files, {'PATTERN.BIN': payload})
                self.assertTrue(report['fat_copies_equal'])

    def test_five_public_profiles_build_as_exact_fat12_d88_volumes(self):
        config = ROOT / 'config/m16/floppy-profiles.json'
        source = json.loads(config.read_text())
        expected = {
            '2d-320': (327680, 40, 2, 8, 0xFF, 0),
            '2d-360': (368640, 40, 2, 9, 0xFD, 0),
            '2dd-640': (655360, 80, 2, 8, 0xFB, 0x10),
            '2dd-720': (737280, 80, 2, 9, 0xF9, 0x10),
            '2hc-1200': (1228800, 80, 2, 15, 0xF1, 0x20),
        }
        self.assertEqual({p['name'] for p in source['profiles']}, set(expected))
        with tempfile.TemporaryDirectory(prefix='m16-floppy-media-') as temporary:
            records = MEDIA.build_profiles(
                config, Path(temporary) / 'disks', 1787814827)
            self.assertEqual(set(records), set(expected))
            for profile in source['profiles']:
                name = profile['name']
                capacity, cylinders, heads, sectors, media_id, disk_type = expected[name]
                record = records[name]
                with self.subTest(profile=name):
                    self.assertEqual(record['raw_capacity_bytes'], capacity)
                    self.assertEqual(profile['guest_media_id'], media_id)
                    self.assertEqual(profile['d88_disk_type'], disk_type)
                    self.assertEqual(profile['geometry']['cylinders'], cylinders)
                    self.assertEqual(profile['geometry']['heads'], heads)
                    self.assertEqual(profile['geometry']['sectors_per_track'], sectors)
                    self.assertEqual(
                        cylinders * heads * sectors * profile['geometry']['bytes_per_sector'],
                        capacity)
                    disk = Path(temporary) / 'disks' / (name + '.d88')
                    self.assertEqual(disk.stat().st_size, record['d88_size'])
                    self.assertEqual(record['filesystem']['files']['M16TEST.TXT']['size'],
                                     record['payload_bytes'])


if __name__ == '__main__':
    unittest.main()
