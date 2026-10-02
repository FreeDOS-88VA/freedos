# SPDX-License-Identifier: GPL-2.0-or-later
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m19/qa'))
from interval_readback import parse_guest


class IntervalReadbackTests(unittest.TestCase):
    CARRIER = {'layout': {'entry': 0x10000,
                          'ranges': {'image': [0x10000, 0x22000],
                                     'bridge': [0x27000, 0x28000],
                                     'scratch': [0x37000, 0x38000],
                                     'ring': [0x38000, 0x39000],
                                     'bridge_stack': [0x3eff0, 0x3fff0]}},
               'split': {'resident_text': [0x1f000, 0x20000],
                         'init': [0x39000, 0x3d000],
                         'init_stack': [0x3d000, 0x3e000]},
               'minimum_runtime_memory_kb': 256, 'size': 0xf000}
    TEXT = '''MEMMAP: validating DOS MCB chain
MCB 2000 M owner=0008 SYSTEM name=SYSTEM   payload=20010-20110 bytes=256 paras=16
MCB 2011 M owner=2012 PSP    name=PROBE    payload=20120-20220 bytes=256 paras=16
MCB 2022 Z owner=0000 FREE   name=-        payload=20230-40000 bytes=130512 paras=8157
Managed MCB range: 20000-40000 bytes (end exclusive)
Blocks: 3; managed bytes: 131072; MCB overhead: 48
Free payload: 130512 bytes; largest free block: 130512 bytes
Allocated payload: 512 bytes; system-owned: 256 bytes
MEMMAP-owned payload (PSP 2012, including owned environment): 256 bytes
Physical/reserved map: unavailable (DOS MCB chain only)
MCB chain: VALID
'''

    def test_interval_owners_and_free_accounting(self):
        summary = parse_guest(self.TEXT, self.CARRIER, 256)
        self.assertEqual(summary['arena']['end'], 256 * 1024)
        self.assertEqual(summary['kernel_work']['owned_payload_bytes'], 256)
        self.assertEqual(summary['owner_count'], 1)
        self.assertEqual(summary['temporary_at_boot']['ring']['start'], 0x38000)
        self.assertEqual(summary['arena']['allocated_payload_bytes'] +
                         summary['arena']['free_payload_bytes'] +
                         summary['arena']['headers'], summary['arena']['bytes'])

    def test_wrong_ram_boundary_bad_owner_gaps_or_summary_are_rejected(self):
        for change, error in (
            (self.TEXT.replace('20000-40000', '20100-40000'), 'arena'),
            (self.TEXT.replace('MCB 2022 Z', 'MCB 2023 Z'), 'header'),
            (self.TEXT.replace('owner=2012 PSP', 'owner=2013 PSP'), 'observer ownership'),
            (self.TEXT.replace('MCB 2022 Z', 'MCB 2022 M'), 'terminal'),
            (self.TEXT.replace('130512 bytes; largest', '130496 bytes; largest'), 'sums'),
            (self.TEXT.replace('MCB chain: VALID', 'MCB chain: INVALID'), 'not reported valid'),
        ):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                parse_guest(change, self.CARRIER, 256)
        with self.assertRaisesRegex(ValueError, 'boundary'):
            parse_guest(self.TEXT, self.CARRIER, 384)
        with self.assertRaisesRegex(ValueError, 'unsupported capacity'):
            parse_guest(self.TEXT, self.CARRIER, 128)
        broken = dict(self.CARRIER, layout={'entry': 0x10000,
                                            'ranges': dict(self.CARRIER['layout']['ranges'], ring=[0x37000, 0x39000])})
        with self.assertRaisesRegex(ValueError, 'placement'):
            parse_guest(self.TEXT, broken, 256)
        with self.assertRaisesRegex(ValueError, 'header count'):
            parse_guest(self.TEXT + 'MCB bad\n', self.CARRIER, 256)


if __name__ == '__main__':
    unittest.main()
