#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Execute pinned component input code with controlled synthetic clock samples."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'components/fdkernel/pc88va/tests'))
import test_m11_consumer as fixture


class RepeatTimingTests(fixture.ConsumerTests):
    def sample(self, tick):
        # Locate the clock in the component's original synthetic harness header,
        # not at a firmware address. Fail if that harness layout changes.
        start = 3 + 13 * 2
        self.assertEqual(self.code[start:start + 7], b'\x02\x01\x00\x00\x00\x00\x00')
        self.cpu.mem_write(fixture.CODE * 16 + start + 3,
                           struct.pack('<I', (tick - 10) & 0xffffffff))

    def value(self):
        return struct.unpack('<H', self.cpu.mem_read(
            fixture.CODE * 16 + self.character, 2))[0]

    def begin_v(self, tick):
        self.assertEqual(self.invoke(self.read, fixture.matrix()), 1)
        self.sample(tick)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 0)
        self.assertEqual(self.value(), ord('v'))

    def test_delay_and_period_cross_32_bit_wrap(self):
        self.begin_v(0xfffffff0)
        for tick in (0xfffffff1, 0xffffffff, 0, 13):
            self.sample(tick)
            self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 1)
        self.sample(14)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 0)
        self.assertEqual(self.value(), ord('v'))
        self.sample(17)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 1)
        self.sample(18)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 0)

    def test_late_poll_produces_one_event_and_no_catchup_burst(self):
        self.begin_v(100)
        self.sample(100000)
        self.assertEqual(self.invoke(self.peek, fixture.matrix(0x46)), 0)
        ports = len(self.read_ports)
        for _ in range(20):
            self.assertEqual(self.invoke(self.peek, fixture.matrix(0x46)), 0)
            self.assertEqual(self.value(), ord('v'))
        self.assertEqual(len(self.read_ports), ports)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 0)
        for tick in (100000, 100001, 100003):
            self.sample(tick)
            self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 1)
        self.sample(100004)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 0)

    def test_release_cancels_even_when_deadline_was_missed(self):
        self.begin_v(100)
        self.sample(100000)
        self.assertEqual(self.invoke(self.read, fixture.matrix()), 1)
        for _ in range(10):
            self.assertEqual(self.invoke(self.read, fixture.matrix()), 1)
        self.sample(200000)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 0)
        self.sample(200029)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 1)
        self.sample(200030)
        self.assertEqual(self.invoke(self.read, fixture.matrix(0x46)), 0)


if __name__ == '__main__':
    unittest.main()
