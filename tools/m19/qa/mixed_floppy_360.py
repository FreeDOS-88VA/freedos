#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prepare/read back disposable 360-KiB 2D-D88 FAT12 mixed-profile B: media.

M19-local public fixture, never part of make m19-disk or the normal D88.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/m19'))
from media import (build_boot_record, build_d88, decode_dos_name,
                   derive_layout, inspect as inspect_d88, parse_d88,
                   set_fat12_entry)

CONFIG = ROOT / 'config/m19/mixed-floppy-360.json'


def verify_config(spec):
    g, f = spec['geometry'], spec['fat12']
    if (spec['schema_version'] != 1 or
            (g['cylinders'], g['heads'], g['sectors_per_track'], g['bytes_per_sector'],
             g['total_sectors'], g['total_bytes']) != (40, 2, 9, 512, 720, 368640) or
            (f['reserved_sectors'], f['fat_count'], f['sectors_per_fat'],
             f['sectors_per_cluster'], f['root_entries'], f['media_descriptor'],
             f['hidden_sectors']) != (1, 2, 2, 2, 112, 0xfd, 0) or
            not spec['volume_label'].isascii() or len(spec['volume_label']) > 11 or
            not 0 <= spec['volume_serial'] <= 0xffffffff):
        raise ValueError('M19 mixed 360-KiB profile differs from accepted public FAT12 geometry')
    first_data = 1 + 2 * 2 + 112 * 32 // 512
    if first_data != 12 or (720 - first_data) // 2 != 354:
        raise ValueError('360-KiB FAT12 layout disagrees')


def d88_profile(spec):
    verify_config(spec)
    geometry = dict(spec['geometry'], physical_sector_id_base=1,
                    track_order='cylinder_major_head_minor', encoding='MFM')
    fs = dict(spec['fat12'], data_clusters=354, fat_bytes_required=534,
              first_data_sector=12, root_directory_sectors=7)
    d88 = dict(header_size=688, sector_header_size=16,
               declared_size=688+720*(16+512), disk_name='M19-QA-360',
               disk_type=0, populated_tracks=80, sector_size_code=2,
               mfm_density_field=0, deleted_data=0, error_status=0,
               rpm_field=0, write_protect=0)
    result = {'geometry': geometry, 'filesystem': fs, 'd88': d88,
              'boot_record': {'placeholder_code': [235, 254, 144],
                              'oem_name': 'FDPC88VA', 'extended_bpb_signature': 41,
                              'filesystem_type': 'FAT12', 'signature_offsets': [510]},
              'image': {'volume_serial': spec['volume_serial'],
                        'volume_label': spec['volume_label']}}
    derive_layout(result)
    return result


def prepare(spec):
    verify_config(spec)
    g, f = spec['geometry'], spec['fat12']
    raw = bytearray(g['total_bytes'])
    boot_spec = {'geometry': dict(g),
                 'filesystem': dict(f),
                 'boot_record': {'placeholder_code': [235, 254, 144],
                                 'oem_name': 'FDPC88VA', 'extended_bpb_signature': 41,
                                 'filesystem_type': 'FAT12', 'signature_offsets': [510]},
                 'image': {'volume_serial': spec['volume_serial'],
                           'volume_label': spec['volume_label']}}
    raw[:512] = build_boot_record(boot_spec)
    fat = bytearray(2 * 512)
    set_fat12_entry(fat, 0, 0xffd)
    set_fat12_entry(fat, 1, 0xfff)
    raw[512:1536] = fat
    raw[1536:2560] = fat
    label = spec['volume_label'].encode('ascii').ljust(11, b' ')
    raw[2560:2571] = label
    raw[2571] = 0x08
    return bytes(raw)


def inspect(raw, spec):
    verify_config(spec)
    if len(raw) != spec['geometry']['total_bytes']:
        raise ValueError('360-KiB raw media length differs')
    if (raw[:3] != b'\xeb\xfe\x90' or raw[510:512] != b'\x55\xaa' or
            struct.unpack_from('<HBHBHHBHHH', raw, 11) !=
            (512, 2, 1, 2, 112, 720, 0xfd, 2, 9, 2) or
            struct.unpack_from('<I', raw, 28)[0] != 0 or
            struct.unpack_from('<I', raw, 39)[0] != spec['volume_serial']):
        raise ValueError('360-KiB BPB, serial or boot sector differs')
    fat = raw[512:1536]
    if raw[1536:2560] != fat:
        raise ValueError('360-KiB FAT copies differ')
    def value(cluster):
        v = int.from_bytes(fat[cluster * 3 // 2:cluster * 3 // 2 + 2], 'little')
        return (v >> (4 if cluster & 1 else 0)) & 0xfff
    if value(0) != 0xffd or value(1) != 0xfff:
        raise ValueError('360-KiB reserved FAT entries differ')
    label = spec['volume_label'].encode('ascii').ljust(11, b' ')
    root, files, owned = raw[2560:2560 + 112*32], {}, set()
    if root[:11] != label or root[11] != 8:
        raise ValueError('360-KiB volume-label root entry differs')
    for offset in range(32, len(root), 32):
        entry = root[offset:offset+32]
        if entry[0] == 0:
            if any(root[offset:]):
                raise ValueError('360-KiB root has hidden live entries')
            break
        if entry[0] == 0xe5:
            continue
        if entry[11] != 0x20 or entry[20:22] != b'\0\0':
            raise ValueError('360-KiB readback contains unsupported entry')
        name = decode_dos_name(entry[:11])
        if name in files:
            raise ValueError('360-KiB root has duplicate names')
        first, size = struct.unpack_from('<HI', entry, 26)
        if size == 0:
            if first:
                raise ValueError('360-KiB empty file owns a cluster')
            files[name] = b''
            continue
        content, cluster = bytearray(), first
        while True:
            if cluster < 2 or cluster > 355 or cluster in owned:
                raise ValueError('360-KiB FAT is cyclic or outside data area')
            owned.add(cluster)
            start = 12*512 + (cluster-2)*1024
            content.extend(raw[start:start+1024])
            next_cluster = value(cluster)
            if 0xff8 <= next_cluster <= 0xfff:
                break
            cluster = next_cluster
        if len(content) - 1024 >= size or size > len(content):
            raise ValueError('360-KiB file size and FAT chain differ')
        files[name] = bytes(content[:size])
    for cluster in range(2, 356):
        if cluster not in owned and value(cluster):
            raise ValueError('360-KiB FAT contains orphan allocation')
    if fat[(356*3+1)//2:] != bytes(len(fat)-(356*3+1)//2):
        raise ValueError('360-KiB unused FAT bytes are nonzero')
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inspect', action='store_true', help='read back an existing disposable image without modifying it')
    args = parser.parse_args()
    target = args.output.resolve()
    if target == ROOT or ROOT in target.parents:
        raise ValueError('QA 360-KiB media must be outside the public source tree')
    spec = json.loads(CONFIG.read_text(encoding='ascii'))
    profile = d88_profile(spec)
    if target.suffix.lower() != '.d88':
        raise ValueError('matched emulator requires 360-KiB 2D-D88, not an unsupported raw .img')
    if args.inspect:
        if not target.is_file():
            raise ValueError('QA media for readback does not exist')
        image = target.read_bytes()
        _, independent = inspect_d88(image, profile)
        _, raw = parse_d88(image, profile, derive_layout(profile))
        if inspect(raw, spec) != independent:
            raise ValueError('2D-D88 FAT readback differs from raw-profile inspector')
        print('Independent M19-local mixed 360-KiB FAT12 readback: {} file(s)'.format(len(independent)))
    else:
        if target.exists():
            raise FileExistsError('QA media output already exists')
        raw = prepare(spec)
        image = build_d88(profile, raw)
        _, independent = inspect_d88(image, profile)
        if inspect(raw, spec) != independent or independent:
            raise ValueError('new mixed-floppy 2D-D88 fixture contains files or disagrees')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(image)
        print('Disposable nonbooting 360-KiB 2D-D88 data disk prepared; NOT a distribution')


if __name__ == '__main__':
    main()
