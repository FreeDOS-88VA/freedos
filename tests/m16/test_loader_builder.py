#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Regression tests for the M16-owned PC-88VA loader builder copies."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / 'tools/m16'))
from build_loader import ProfileError, build_stage, validate_overlay
from loader_profile import definitions


class LoaderBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(
            (ROOT / 'config/m16/va-fixed-loader-profile-test.json').read_text())

    def test_m16_synthetic_overlay_is_bound_to_the_expected_regions(self):
        profile = self.profile
        self.assertEqual(validate_overlay(profile), profile)
        values = definitions(profile['layout'])
        self.assertEqual(values['PC88VA_INITIAL_LOAD_SEGMENT'], 0x1340)
        self.assertEqual(values['PC88VA_LOW_STAGING_SEGMENT'], 0x1340)
        self.assertEqual(values['S2_KERNEL_ALLOCATION_SEGMENT'], 0x3000)
        self.assertEqual(values['S2_KERNEL_IN_PLACE'], 0)

    def test_overlay_schema_and_callback_fail_closed(self):
        for mutate in (
                lambda value: value.update(extra=1),
                lambda value: value.update(schema_version=True),
                lambda value: value.update(firmware_callback='%include "private.inc"')):
            bad = copy.deepcopy(self.profile)
            mutate(bad)
            with self.subTest(profile=bad):
                with self.assertRaises(ProfileError):
                    validate_overlay(bad)

    def test_both_loader_stages_build_identically_from_component_sources(self):
        outputs = []
        with tempfile.TemporaryDirectory(prefix='m16-loader-builder-') as directory:
            root = Path(directory)
            for number in (1, 2):
                out = root / str(number)
                stage2 = build_stage(self.profile, out, 2)
                extent = {
                    'first_lba': 11,
                    'sector_count': (stage2['size'] + 1023) // 1024,
                    'file_size': stage2['size'],
                }
                stage1 = build_stage(self.profile, out, 1, extent)
                outputs.append((stage1, stage2,
                                (out / 'stage1.bin').read_bytes(),
                                (out / 'stage2.bin').read_bytes()))
            self.assertEqual(outputs[0], outputs[1])

    def test_builder_does_not_overwrite_an_existing_stage(self):
        with tempfile.TemporaryDirectory(prefix='m16-loader-overwrite-') as directory:
            out = Path(directory)
            build_stage(self.profile, out, 2)
            before = (out / 'stage2.bin').read_bytes()
            with self.assertRaises(ProfileError):
                build_stage(self.profile, out, 2)
            self.assertEqual((out / 'stage2.bin').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
