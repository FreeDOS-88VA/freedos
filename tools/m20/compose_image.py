#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Create fresh M20 FAT12/D88 media from source-built payloads, without a seed.

Maintained M20 copy of the integrated M17 composer present at M18 START_SHA
`d81bba18f0e4793d7165fb0acfdf7e229e160c83`; it imports only tools/m20 helpers.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m20'))
from media import build_boot_record, build_d88, build_directory_entry, set_fat12_entry
from media import derive_layout, inspect
from build_loader import build_stage, validate_overlay


def compose(payloads, overlay, output, epoch):
    spec = json.loads((ROOT / 'config/m20/media.json').read_text())
    spec['d88']['disk_name'] = 'FDOS-PC88VA-M20'
    spec['image']['volume_label'] = 'PC88VA-M20'
    layout = derive_layout(spec)
    geo, fs = spec['geometry'], spec['filesystem']
    bps = geo['bytes_per_sector']
    # One directory level is supported: "DIR/FILE" payload names.
    if any(name.count('/') > 1 for name in payloads):
        raise ValueError('Payload paths deeper than one directory are unsupported')
    subdirs = sorted({name.split('/')[0] for name in payloads if '/' in name})
    if set(subdirs) & set(payloads):
        raise ValueError('A payload name collides with a directory name')
    root_files = [name for name in payloads if '/' not in name]
    if len(root_files) + len(subdirs) + 1 > fs['root_entries']:
        raise ValueError('Too many directory entries including the volume label')
    raw = bytearray(geo['total_bytes'])
    fat = bytearray(fs['sectors_per_fat'] * bps)
    set_fat12_entry(fat, 0, 0xf00 | fs['media_descriptor'])
    set_fat12_entry(fat, 1, 0xfff)
    root_start = (fs['reserved_sectors'] + fs['fat_count'] * fs['sectors_per_fat']) * bps
    allocations, cluster = {}, 2
    label = spec['image']['volume_label'].encode('ascii')
    if not label or len(label) > 11:
        raise ValueError('Volume label must be 1..11 ASCII bytes')
    volume_entry = bytearray(32)
    volume_entry[:11] = label.ljust(11, b' ')
    volume_entry[11] = 0x08
    raw[root_start:root_start + 32] = volume_entry
    root_index = 1
    # Stage 1 reads a contiguous LOADER.BIN extent derived from this allocation.
    names = ['LOADER.BIN'] + sorted((set(root_files) | set(subdirs)) - {'LOADER.BIN'})

    def allocate(data):
        nonlocal cluster
        count = (len(data) + bps - 1) // bps
        if cluster + count > layout['data_clusters'] + 2:
            raise ValueError('Payloads exceed FAT12 capacity')
        first = cluster if count else 0
        for n in range(count):
            set_fat12_entry(fat, cluster + n, cluster + n + 1 if n + 1 < count else 0xfff)
            offset = (layout['first_data_sector'] + cluster + n - 2) * bps
            raw[offset:offset + bps] = data[n*bps:(n+1)*bps].ljust(bps, b'\0')
        cluster += count
        return first, count

    for name in names:
        if name in subdirs:
            members = sorted(n for n in payloads if n.startswith(name + '/'))
            # Reserve the directory clusters, then allocate its files after them.
            dir_count = ((len(members) + 2) * 32 + bps - 1) // bps
            first, _ = allocate(bytes(dir_count * bps))
            table = bytearray(dir_count * bps)
            for index, dot in enumerate(('.', '..')):
                entry = bytearray(build_directory_entry(
                    dict(dos_name='X', size=0, source_date_epoch=epoch), first if dot == '.' else 0)[0])
                entry[:11] = dot.encode('ascii').ljust(11, b' ')
                entry[11] = 0x10
                table[index*32:(index+1)*32] = entry
            for index, member in enumerate(members, 2):
                data = payloads[member]
                start = cluster
                member_first, member_count = allocate(data)
                allocations[member] = dict(first_lba=layout['first_data_sector'] + start - 2,
                                           sector_count=member_count, file_size=len(data))
                entry, _ = build_directory_entry(dict(dos_name=member.split('/')[1], size=len(data),
                                                      source_date_epoch=epoch), member_first)
                table[index*32:(index+1)*32] = entry
            offset = (layout['first_data_sector'] + first - 2) * bps
            raw[offset:offset + len(table)] = table
            entry = bytearray(build_directory_entry(dict(dos_name=name, size=0, source_date_epoch=epoch), first)[0])
            entry[11] = 0x10
        else:
            data = payloads[name]
            start = cluster
            first, count = allocate(data)
            entry, _ = build_directory_entry(dict(dos_name=name, size=len(data), source_date_epoch=epoch), first)
            allocations[name] = dict(first_lba=layout['first_data_sector'] + start - 2,
                                     sector_count=count, file_size=len(data))
        raw[root_start + root_index*32:root_start + (root_index+1)*32] = entry
        root_index += 1
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


def data_disk_spec(disk_name, volume_label):
    """Return the native 2HD media profile with a data disk's D88 name and label."""
    spec = json.loads((ROOT / 'config/m20/media.json').read_text())
    spec['d88']['disk_name'] = disk_name
    spec['image']['volume_label'] = volume_label
    return spec


def compose_data(payloads, output, epoch, disk_name, volume_label, stem='util'):
    """Compose a non-bootable native 2HD FAT12 data disk for drive B:.

    Same geometry and FAT12 layout as the system disk, with the public data
    boot record (no loader) used for disposable B: targets.
    """
    spec = data_disk_spec(disk_name, volume_label)
    layout = derive_layout(spec)
    geo, fs = spec['geometry'], spec['filesystem']
    bps = geo['bytes_per_sector']
    # Data disks hold root-directory files only.
    if any('/' in name for name in payloads):
        raise ValueError('Data disk payloads must be root-directory files')
    if len(payloads) + 1 > fs['root_entries']:
        raise ValueError('Too many directory entries including the volume label')
    label = volume_label.encode('ascii')
    if not label or len(label) > 11:
        raise ValueError('Volume label must be 1..11 ASCII bytes')
    raw = bytearray(geo['total_bytes'])
    raw[:bps] = build_boot_record(spec)
    fat = bytearray(fs['sectors_per_fat'] * bps)
    set_fat12_entry(fat, 0, 0xf00 | fs['media_descriptor'])
    set_fat12_entry(fat, 1, 0xfff)
    root_start = (fs['reserved_sectors'] + fs['fat_count'] * fs['sectors_per_fat']) * bps
    volume_entry = bytearray(32)
    volume_entry[:11] = label.ljust(11, b' ')
    volume_entry[11] = 0x08
    raw[root_start:root_start + 32] = volume_entry
    allocations, cluster, root_index = {}, 2, 1
    for name in sorted(payloads):
        data = payloads[name]
        count = (len(data) + bps - 1) // bps
        if cluster + count > layout['data_clusters'] + 2:
            raise ValueError('Data disk payloads exceed FAT12 capacity')
        first = cluster if count else 0
        for n in range(count):
            set_fat12_entry(fat, cluster + n, cluster + n + 1 if n + 1 < count else 0xfff)
            offset = (layout['first_data_sector'] + cluster + n - 2) * bps
            raw[offset:offset + bps] = data[n*bps:(n+1)*bps].ljust(bps, b'\0')
        entry, _ = build_directory_entry(dict(dos_name=name, size=len(data), source_date_epoch=epoch), first)
        raw[root_start + root_index*32:root_start + (root_index+1)*32] = entry
        root_index += 1
        allocations[name] = dict(first_lba=layout['first_data_sector'] + cluster - 2,
                                 sector_count=count, file_size=len(data))
        cluster += count
    for n in range(fs['fat_count']):
        offset = (fs['reserved_sectors'] + n * fs['sectors_per_fat']) * bps
        raw[offset:offset + len(fat)] = fat
    d88 = build_d88(spec, bytes(raw))
    report, files = inspect(d88, spec)
    if files != payloads or not report['fat_copies_equal']:
        raise ValueError('Fresh data disk readback differs from source-built payloads')
    (output / (stem + '.d88')).write_bytes(d88)
    (output / (stem + '-media.json')).write_text(json.dumps({'allocations': allocations, 'filesystem': report}, indent=2)+'\n')
    return d88
