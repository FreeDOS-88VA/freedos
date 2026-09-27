#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build fresh FAT12 D88 fixtures for the M16 floppy profiles."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m16'))
from media import (build_boot_record, build_d88, build_directory_entry,
                   derive_layout, inspect, parse_d88, set_fat12_entry)


def profile_spec(profile, shared, source_date_epoch):
    geometry = dict(profile['geometry'])
    geometry['encoding'] = 'MFM'
    geometry['track_order'] = 'cylinder_major_head_minor'
    geometry['total_sectors'] = (geometry['cylinders'] * geometry['heads'] *
                                 geometry['sectors_per_track'])
    geometry['total_bytes'] = geometry['total_sectors'] * geometry['bytes_per_sector']

    filesystem = dict(profile['filesystem'])
    bps = geometry['bytes_per_sector']
    root_sectors = (filesystem['root_entries'] * 32 + bps - 1) // bps
    first_data = (filesystem['reserved_sectors'] +
                  filesystem['fat_count'] * filesystem['sectors_per_fat'] + root_sectors)
    data_sectors = geometry['total_sectors'] - first_data
    if data_sectors <= 0 or data_sectors % filesystem['sectors_per_cluster']:
        raise ValueError('M16 profile does not have an integral FAT12 data area: ' +
                         profile['name'])
    clusters = data_sectors // filesystem['sectors_per_cluster']
    filesystem.update({
        'fat_type': 'FAT12',
        'hidden_sectors': 0,
        'data_clusters': clusters,
        'fat_bytes_required': ((clusters + 2) * 3 + 1) // 2,
        'first_data_sector': first_data,
        'root_directory_sectors': root_sectors,
        'fat_timestamp_policy': 'source_date_epoch_utc_truncated_to_even_second',
        'unallocated_data_policy': 'zero',
    })

    d88 = dict(shared['d88'])
    d88.update({
        'disk_name': 'M16-' + profile['name'].upper(),
        'disk_type': profile['d88_disk_type'],
        'populated_tracks': geometry['cylinders'] * geometry['heads'],
        'track_table_entries': 164,
        'declared_size': (shared['d88']['header_size'] +
                          geometry['total_sectors'] *
                          (shared['d88']['sector_header_size'] + bps)),
    })
    spec = {
        'geometry': geometry,
        'filesystem': filesystem,
        'd88': d88,
        'boot_record': dict(shared['boot_record']),
        'image': {
            'volume_label': profile['image']['volume_label'],
            'volume_serial': profile['image']['volume_serial'],
        },
        'build': {'source_date_epoch': source_date_epoch},
    }
    derive_layout(spec)
    if profile['guest_media_id'] != filesystem['media_descriptor']:
        raise ValueError('Guest media ID and FAT media descriptor differ: ' +
                         profile['name'])
    return spec


def profile_payload(profile, template):
    geometry = profile['geometry']
    return template.format(
        name=profile['name'],
        cylinders=geometry['cylinders'],
        heads=geometry['heads'],
        sectors_per_track=geometry['sectors_per_track'],
        bytes_per_sector=geometry['bytes_per_sector'],
        guest_media_id=profile['guest_media_id'],
    ).encode('ascii')


def build_volume(spec, dos_name, content, source_date_epoch):
    geometry, filesystem = spec['geometry'], spec['filesystem']
    layout = derive_layout(spec)
    bps = geometry['bytes_per_sector']
    raw = bytearray(geometry['total_bytes'])
    fat = bytearray(filesystem['sectors_per_fat'] * bps)
    set_fat12_entry(fat, 0, 0xF00 | filesystem['media_descriptor'])
    set_fat12_entry(fat, 1, 0xFFF)

    root_start = (filesystem['reserved_sectors'] +
                  filesystem['fat_count'] * filesystem['sectors_per_fat']) * bps
    label = spec['image']['volume_label'].encode('ascii')
    if len(label) > 11:
        raise ValueError('M16 volume label exceeds 11 bytes')
    root = bytearray(layout['root_directory_sectors'] * bps)
    root[0:11] = label.ljust(11, b' ')
    root[11] = 0x08

    cluster_bytes = bps * filesystem['sectors_per_cluster']
    allocation_count = (len(content) + cluster_bytes - 1) // cluster_bytes
    if allocation_count > layout['data_clusters']:
        raise ValueError('M16 test file exceeds the FAT12 data area')
    first_cluster = 2 if allocation_count else 0
    for index in range(allocation_count):
        cluster = first_cluster + index
        following = cluster + 1 if index + 1 < allocation_count else 0xFFF
        set_fat12_entry(fat, cluster, following)
        first_lba = (layout['first_data_sector'] +
                     (cluster - 2) * filesystem['sectors_per_cluster'])
        start = first_lba * bps
        chunk = content[index * cluster_bytes:(index + 1) * cluster_bytes]
        raw[start:start + cluster_bytes] = chunk.ljust(cluster_bytes, b'\0')

    entry, _ = build_directory_entry({
        'dos_name': dos_name,
        'size': len(content),
        'source_date_epoch': source_date_epoch,
    }, first_cluster)
    root[32:64] = entry
    raw[root_start:root_start + len(root)] = root
    for copy in range(filesystem['fat_count']):
        offset = (filesystem['reserved_sectors'] +
                  copy * filesystem['sectors_per_fat']) * bps
        raw[offset:offset + len(fat)] = fat
    raw[:bps] = build_boot_record(spec)
    image = build_d88(spec, bytes(raw))
    report, files = inspect(image, spec)
    if files != {dos_name: content} or not report['fat_copies_equal']:
        raise ValueError('M16 D88 readback differs from its generated FAT12 payload')
    return image, report


def build_boundary_volume(spec, source_date_epoch):
    """Place an original file across tracks and in the last data cluster."""
    content = bytes((i * 37 + i // 251) & 255 for i in range(33792))
    image, _ = build_volume(spec, 'PATTERN.BIN', content, source_date_epoch)
    layout = derive_layout(spec)
    _, raw_bytes = parse_d88(image, spec, layout)
    raw = bytearray(raw_bytes)
    fs = spec['filesystem']
    bps = spec['geometry']['bytes_per_sector']
    cluster_bytes = bps * fs['sectors_per_cluster']
    if len(content) % cluster_bytes:
        raise ValueError('Boundary payload must fill its last cluster')
    count = len(content) // cluster_bytes
    previous_last = count + 1
    last = layout['data_clusters'] + 1
    if count < 2 or previous_last >= last:
        raise ValueError('Boundary fixture requires spare data clusters')
    def offset(cluster):
        return layout['first_data_sector'] * bps + (cluster - 2) * cluster_bytes
    raw[offset(last):offset(last) + cluster_bytes] = raw[
        offset(previous_last):offset(previous_last) + cluster_bytes]
    raw[offset(previous_last):offset(previous_last) + cluster_bytes] = bytes(cluster_bytes)
    fat_size = fs['sectors_per_fat'] * bps
    for copy in range(fs['fat_count']):
        start = (fs['reserved_sectors'] + copy * fs['sectors_per_fat']) * bps
        fat = raw[start:start + fat_size]
        set_fat12_entry(fat, previous_last - 1, last)
        set_fat12_entry(fat, previous_last, 0)
        set_fat12_entry(fat, last, 0xFFF)
        raw[start:start + fat_size] = fat
    image = build_d88(spec, bytes(raw))
    report, files = inspect(image, spec)
    if (files != {'PATTERN.BIN': content} or
            report['files']['PATTERN.BIN']['clusters'][-1] != last):
        raise ValueError('Boundary fixture readback differs')
    return image, report


def build_profiles(config_path, output, source_date_epoch, boundary=False):
    config = json.loads(Path(config_path).read_text())
    if config.get('schema_version') != 1 or len(config.get('profiles', [])) != 5:
        raise ValueError('M16 floppy profile set must contain the five required formats')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    names = set()
    for profile in config['profiles']:
        name = profile['name']
        if name in names:
            raise ValueError('Duplicate M16 floppy profile: ' + name)
        names.add(name)
        spec = profile_spec(profile, config, source_date_epoch)
        content = profile_payload(profile, config['test_file']['content_template'])
        if boundary:
            image, report = build_boundary_volume(spec, source_date_epoch)
            content = inspect(image, spec)[1]['PATTERN.BIN']
        else:
            image, report = build_volume(
                spec, config['test_file']['dos_name'], content, source_date_epoch)
        target = output / (name + '.d88')
        if target.exists():
            raise ValueError('Refusing to overwrite M16 floppy media: ' + str(target))
        target.write_bytes(image)
        records[name] = {
            'guest_media_id': profile['guest_media_id'],
            'geometry': profile['geometry'],
            'payload_bytes': len(content),
            'raw_capacity_bytes': spec['geometry']['total_bytes'],
            'd88_size': len(image),
            'd88_sha256': hashlib.sha256(image).hexdigest(),
            'filesystem': report,
        }
    (output / 'profiles.json').write_text(json.dumps(records, indent=2) + '\n')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/m16/floppy-profiles.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-date-epoch', type=int, default=1787814827)
    parser.add_argument('--boundary', action='store_true',
                        help='Generate fragmented files through the final data sector')
    args = parser.parse_args()
    records = build_profiles(args.config, args.output, args.source_date_epoch, args.boundary)
    for name, record in records.items():
        print(f"{name}: {record['raw_capacity_bytes']} bytes, D88 SHA-256 {record['d88_sha256']}")


if __name__ == '__main__':
    main()
