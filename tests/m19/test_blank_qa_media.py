# SPDX-License-Identifier: GPL-2.0-or-later
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m19'))
sys.path.insert(0, str(ROOT / 'tools/m19/qa'))
from media import inspect, derive_layout, parse_d88
import blank_data_media as qa


class BlankDataMediaTests(unittest.TestCase):
    def test_new_target_is_deterministic_empty_nonbooting_public_geometry(self):
        spec = json.loads((ROOT / 'config/m19/media.json').read_text())
        before = json.dumps(spec, sort_keys=True)
        first, second = qa.blank_data_media(spec), qa.blank_data_media(spec)
        self.assertEqual(first, second)
        self.assertEqual(before, json.dumps(spec, sort_keys=True))
        fixture = json.loads(json.dumps(spec))
        fixture['d88']['disk_name'] = 'M19-QA-DATA'
        fixture['image']['volume_label'] = 'M19QA-B'
        report, files = inspect(first, fixture)
        self.assertEqual(files, {})
        self.assertEqual(report['volume_label'], 'M19QA-B')
        self.assertEqual(len(report['free_clusters']), fixture['filesystem']['data_clusters'])
        self.assertNotEqual(first[:17], b'FDOS-PC88VA-M19'.ljust(17, b'\0'))
        _, raw = parse_d88(first, fixture, derive_layout(fixture))
        self.assertEqual(raw[:3], b'\xeb\xfe\x90')

    def test_refuses_overwrite_and_public_output_location(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'blank.d88'
            argv = ['blank_data_media.py', '--output', str(destination)]
            with patch('sys.argv', argv):
                qa.main()
            with patch('sys.argv', argv), self.assertRaises(FileExistsError):
                qa.main()
            argv[-1] = str(ROOT / 'blank-public.d88')
            with patch('sys.argv', argv), self.assertRaisesRegex(ValueError, 'outside the public source'):
                qa.main()
            self.assertFalse((ROOT / 'blank-public.d88').exists())


if __name__ == '__main__':
    unittest.main()
