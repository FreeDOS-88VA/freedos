#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Create fresh FAT12/D88 media from source-built payloads, without a seed."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m17'))
from media import build_boot_record, build_d88, build_directory_entry, set_fat12_entry
from media import derive_layout, inspect
from build_loader import build_stage, validate_overlay


def compose(payloads, overlay, output, epoch):
    spec = json.loads((ROOT / 'config/m17/media.json').read_text())
    spec['d88']['disk_name'] = 'FDOS-PC88VA-M17'
    spec['image']['volume_label'] = 'PC88VA-M17'
    layout = derive_layout(spec)
    geo, fs = spec['geometry'], spec['filesystem']
    bps = geo['bytes_per_sector']
    if len(payloads) > fs['root_entries']:
        raise ValueError('Too many directory entries')
    raw = bytearray(geo['total_bytes'])
    fat = bytearray(fs['sectors_per_fat'] * bps)
    set_fat12_entry(fat, 0, 0xf00 | fs['media_descriptor'])
    set_fat12_entry(fat, 1, 0xfff)
    root_start = (fs['reserved_sectors'] + fs['fat_count'] * fs['sectors_per_fat']) * bps
    allocations, cluster = {}, 2
    # Stage 1 reads a contiguous LOADER.BIN extent derived from this allocation.
    names = ['LOADER.BIN'] + sorted(set(payloads) - {'LOADER.BIN'})
    for index, name in enumerate(names):
        data = payloads[name]
        count = (len(data) + bps - 1) // bps
        if cluster + count > layout['data_clusters'] + 2:
            raise ValueError('Payloads exceed FAT12 capacity')
        first = cluster if count else 0
        for n in range(count):
            set_fat12_entry(fat, cluster + n, cluster + n + 1 if n + 1 < count else 0xfff)
            offset = (layout['first_data_sector'] + cluster + n - 2) * bps
            raw[offset:offset + bps] = data[n*bps:(n+1)*bps].ljust(bps, b'\0')
        entry, _ = build_directory_entry(dict(dos_name=name, size=len(data), source_date_epoch=epoch), first)
        raw[root_start + index*32:root_start + (index+1)*32] = entry
        allocations[name] = dict(first_lba=layout['first_data_sector'] + cluster - 2,
                                 sector_count=count, file_size=len(data))
        cluster += count
    for n in range(fs['fat_count']):
        offset = (fs['reserved_sectors'] + n * fs['sectors_per_fat']) * bps
        raw[offset:offset + len(fat)] = fat
    stage_dir = output / 'stage1'
    stage_dir.mkdir()
    build_stage(validate_overlay(overlay), stage_dir, 1, allocations['LOADER.BIN'])
    boot = bytearray((stage_dir / 'stage1.bin').read_bytes())
    if len(boot) != bps:
        raise ValueError('Stage 1 must occupy exactly one sector')
    boot[3:62] = build_boot_record(spec)[3:62]
    for offset in spec['boot_record']['signature_offsets']:
        boot[offset:offset+2] = bytes.fromhex('55aa')
    raw[:bps] = boot
    d88 = build_d88(spec, bytes(raw))
    report, files = inspect(d88, spec)
    if files != payloads or not report['fat_copies_equal']:
        raise ValueError('Fresh media readback differs from source-built payloads')
    (output / 'media.d88').write_bytes(d88)
    (output / 'media.json').write_text(json.dumps({'allocations': allocations, 'filesystem': report}, indent=2)+'\n')
    return d88
