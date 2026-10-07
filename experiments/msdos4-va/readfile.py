#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Copy a root-directory file out of an experiment D88 image.

Maintained copy of experiments/msdos2-va/readfile.py.
"""
import argparse
from pathlib import Path
import struct
import sys

SECTOR, SPT, HEADS = 1024, 8, 2


def raw_image(d88):
    """Return the logical 2HD image from a D88 file."""
    sectors = {}
    for track in range(164):
        offset = struct.unpack_from('<I', d88, 0x20 + 4 * track)[0]
        if not offset:
            continue
        count = struct.unpack_from('<H', d88, offset + 4)[0]
        for _ in range(count):
            c, h, r, _, _ = struct.unpack_from('<BBBBH', d88, offset)
            size = struct.unpack_from('<H', d88, offset + 14)[0]
            sectors[(c, h, r)] = d88[offset + 16:offset + 16 + size]
            offset += 16 + size
    cylinders = max(c for c, _, _ in sectors) + 1
    return b''.join(sectors.get((c, h, r), bytes(SECTOR))
                    for c in range(cylinders) for h in range(HEADS) for r in range(1, SPT + 1))


def read_file(raw, name):
    bps, _, reserved, fats, entries, _, _, fat_sectors = struct.unpack_from('<HBHBHHBH', raw, 11)
    fat = raw[reserved * bps:(reserved + fat_sectors) * bps]
    root = (reserved + fats * fat_sectors) * bps
    data = root + entries * 32
    stem, _, ext = name.upper().partition('.')
    wanted = stem.ljust(8).encode() + ext.ljust(3).encode()
    for index in range(entries):
        entry = raw[root + index * 32:root + (index + 1) * 32]
        if entry[0] == 0:
            break
        if entry[:11] != wanted:
            continue
        cluster, size = struct.unpack_from('<HI', entry, 26)
        out = bytearray()
        while 2 <= cluster < 0xFF8:
            out += raw[data + (cluster - 2) * bps:data + (cluster - 1) * bps]
            value = struct.unpack_from('<H', fat, cluster * 3 // 2)[0]
            cluster = value >> 4 if cluster & 1 else value & 0xFFF
        return bytes(out[:size])
    raise SystemExit('not found: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('name')
    args = parser.parse_args()
    sys.stdout.buffer.write(read_file(raw_image(args.image.read_bytes()), args.name))


if __name__ == '__main__':
    main()
