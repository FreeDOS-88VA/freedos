#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Create a disposable native 2HD FAT12 B: target from M19 public settings.

This is not a boot disk and is not an input to make m19-disk. Never use the
released A: source disk as a FORMAT/SYS destination.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/m19'))
from media import build_boot_record, build_d88, derive_layout, inspect, set_fat12_entry


def blank_data_media(spec):
    profile = json.loads(json.dumps(spec))
    profile['d88']['disk_name'] = 'M19-QA-DATA'
    profile['image']['volume_label'] = 'M19QA-B'
    layout = derive_layout(profile)
    bps, fs = profile['geometry']['bytes_per_sector'], profile['filesystem']
    raw = bytearray(profile['geometry']['total_bytes'])
    raw[:bps] = build_boot_record(profile)
    fat = bytearray(fs['sectors_per_fat'] * bps)
    set_fat12_entry(fat, 0, 0xf00 | fs['media_descriptor'])
    set_fat12_entry(fat, 1, 0xfff)
    for copy in range(fs['fat_count']):
        low = (fs['reserved_sectors'] + copy * fs['sectors_per_fat']) * bps
        raw[low:low+len(fat)] = fat
    root = (fs['reserved_sectors'] + fs['fat_count'] * fs['sectors_per_fat']) * bps
    label = bytearray(32)
    label[:11] = profile['image']['volume_label'].encode('ascii').ljust(11, b' ')
    label[11] = 8
    raw[root:root + 32] = label
    image = build_d88(profile, bytes(raw))
    report, files = inspect(image, profile)
    if files or len(report['free_clusters']) != layout['data_clusters'] or not report['fat_copies_equal']:
        raise ValueError('blank native 2HD target failed independent readback')
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('disposable target disk must be outside the public source tree')
    spec = json.loads((ROOT / 'config/m19/media.json').read_text())
    image = blank_data_media(spec)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as target:
        target.write(image)
    print('Disposable public-profile native 2HD B: target prepared; NOT a distribution')


if __name__ == '__main__':
    main()
