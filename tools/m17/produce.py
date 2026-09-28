#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Produce deterministic, public, nonbootable M17 FAT12/FAT16 fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from contracts import fat_layout, load, validate_profile


def expected_files():
    return {
        'README.TXT': b'M17 public synthetic storage fixture. Data only; runtime support is not implied.\r\n',
        'PATTERN.BIN': bytes(((i * 37) ^ (i >> 8) ^ 0xa5) & 0xff
                            for i in range(70123)),
        'CROSS.BIN': bytes((i * 13 + 7) & 0xff for i in range(4097)),
        'LAST.BIN': b'Last data clusters are deliberately allocated last.\r\n' +
                    bytes((i * 19 + 0x31) & 0xff for i in range(1507)),
        'SUBDIR/INNER.TXT': b'Nested directory content for independent readback.\r\n' +
                            bytes((i * 5 + 0x42) & 0xff for i in range(269)),
    }


def _entry(name, attr, cluster, size):
    entry = bytearray(32)
    if name in ('.', '..'):
        encoded = name.ljust(11)
    else:
        stem, dot, extension = name.partition('.')
        if len(stem) > 8 or len(extension) > 3 or (dot and not extension):
            raise ValueError('fixture name is not 8.3: ' + name)
        encoded = stem.ljust(8) + extension.ljust(3)
    entry[:11] = encoded.encode('ascii')
    entry[11] = attr
    # Fixed 2026-09-27 00:00:00 DOS timestamps; no host clock enters output.
    date = ((2026 - 1980) << 9) | (9 << 5) | 27
    struct.pack_into('<HHHI', entry, 22, 0, date, cluster, size)
    return entry


def _fat_set(fat, bits, cluster, value):
    if bits == 16:
        struct.pack_into('<H', fat, cluster * 2, value)
        return
    offset = cluster + cluster // 2
    word = int.from_bytes(fat[offset:offset + 2], 'little')
    if cluster & 1:
        word = (word & 0x000f) | (value << 4)
    else:
        word = (word & 0xf000) | value
    fat[offset:offset + 2] = word.to_bytes(2, 'little')


def _chs(lba, sectors_per_track, heads):
    cylinder, within_cylinder = divmod(lba, sectors_per_track * heads)
    head, sector0 = divmod(within_cylinder, sectors_per_track)
    if cylinder > 1023:
        return b'\xff\xff\xff'
    return bytes((cylinder & 0xff,
                  ((cylinder >> 2) & 0xc0) | head,
                  sector0 + 1))


def _boot_sector(profile, layout):
    volume = profile['volume']
    bps = volume['logical_sector_bytes']
    total = volume['total_logical_sectors']
    boot = bytearray(bps)
    boot[:11] = b'\xeb\x3c\x90PC88VA17'
    struct.pack_into(
        '<HBHBHHBHHHII', boot, 11,
        bps, volume['sectors_per_cluster'], volume['reserved_sectors'],
        volume['fat_count'], volume['root_entries'],
        total if total <= 0xffff else 0, volume['media_descriptor'],
        layout['fat_sectors'], volume['bpb_sectors_per_track'],
        volume['bpb_heads'], volume['hidden_sectors'],
        total if total > 0xffff else 0)
    boot[36] = 0x80 if profile['device']['transport'] != 'fdd' else 0
    boot[38] = 0x29
    struct.pack_into('<I', boot, 39, volume['volume_serial'])
    boot[43:54] = volume['volume_label'].ljust(11).encode('ascii')
    boot[54:62] = ('FAT%d' % volume['fat_bits']).ljust(8).encode('ascii')
    boot[62:66] = b'\xfa\xf4\xeb\xfd'  # CLI; HLT; loop. This is not boot media.
    boot[510:512] = b'\x55\xaa'
    return boot


def _build_volume(profile, files):
    volume_profile = profile['volume']
    layout = fat_layout(profile)
    bps = volume_profile['logical_sector_bytes']
    spc = volume_profile['sectors_per_cluster']
    cluster_bytes = spc * bps
    volume = bytearray(volume_profile['total_logical_sectors'] * bps)
    volume[:bps] = _boot_sector(profile, layout)

    fat_bits = volume_profile['fat_bits']
    eoc = (1 << fat_bits) - 1
    fat = bytearray(layout['fat_sectors'] * bps)
    _fat_set(fat, fat_bits, 0, (eoc & ~0xff) | volume_profile['media_descriptor'])
    _fat_set(fat, fat_bits, 1, eoc)

    free = set(range(2, layout['cluster_count'] + 2))
    chains = {}

    def allocate(size, fragmented=False, last=False):
        count = max(1, (size + cluster_bytes - 1) // cluster_bytes)
        available = sorted(free)
        if count > len(available):
            raise ValueError('fixture files exceed data-cluster capacity')
        if last:
            chain = available[-count:]
        elif fragmented:
            chain = available[::2][:count]
            if len(chain) < count:
                chosen = set(chain)
                chain.extend(n for n in available if n not in chosen and len(chain) < count)
        else:
            chain = available[:count]
        free.difference_update(chain)
        return chain

    ordered_names = ('README.TXT', 'PATTERN.BIN', 'CROSS.BIN', 'LAST.BIN')
    for name in ordered_names:
        content = files[name]
        chains[name] = allocate(len(content), fragmented=(name in {'PATTERN.BIN', 'CROSS.BIN'}),
                                last=(name == 'LAST.BIN'))
    directory_cluster = allocate(cluster_bytes)[0]
    chains['SUBDIR'] = [directory_cluster]
    chains['SUBDIR/INNER.TXT'] = allocate(len(files['SUBDIR/INNER.TXT']))

    data_offset = layout['data_start_sector'] * bps
    for name, chain in chains.items():
        for index, cluster in enumerate(chain):
            next_cluster = chain[index + 1] if index + 1 < len(chain) else eoc
            _fat_set(fat, fat_bits, cluster, next_cluster)
            if name in files:
                payload = files[name][index * cluster_bytes:(index + 1) * cluster_bytes]
            elif name == 'SUBDIR':
                entries = (_entry('.', 0x10, directory_cluster, 0) +
                           _entry('..', 0x10, 0, 0) +
                           _entry('INNER.TXT', 0x20,
                                  chains['SUBDIR/INNER.TXT'][0],
                                  len(files['SUBDIR/INNER.TXT'])))
                payload = entries[index * cluster_bytes:(index + 1) * cluster_bytes]
            else:
                payload = b''
            offset = data_offset + (cluster - 2) * cluster_bytes
            volume[offset:offset + len(payload)] = payload

    root = bytearray(layout['root_sectors'] * bps)
    root[:11] = volume_profile['volume_label'].ljust(11).encode('ascii')
    root[11] = 0x08
    root[32:64] = _entry('README.TXT', 0x20, chains['README.TXT'][0],
                         len(files['README.TXT']))
    root[64:96] = _entry('PATTERN.BIN', 0x20, chains['PATTERN.BIN'][0],
                         len(files['PATTERN.BIN']))
    root[96:128] = _entry('CROSS.BIN', 0x20, chains['CROSS.BIN'][0],
                         len(files['CROSS.BIN']))
    root[128:160] = _entry('LAST.BIN', 0x20, chains['LAST.BIN'][0],
                           len(files['LAST.BIN']))
    root[160:192] = _entry('SUBDIR', 0x10, directory_cluster, 0)
    fat_offset = volume_profile['reserved_sectors'] * bps
    volume[fat_offset:fat_offset + len(fat)] = fat
    volume[fat_offset + len(fat):fat_offset + 2 * len(fat)] = fat
    root_offset = (volume_profile['reserved_sectors'] +
                   volume_profile['fat_count'] * layout['fat_sectors']) * bps
    volume[root_offset:root_offset + len(root)] = root

    if max(chains['LAST.BIN']) != layout['cluster_count'] + 1:
        raise ValueError('LAST.BIN did not reach the last data cluster')
    if all(b == a + 1 for a, b in zip(chains['PATTERN.BIN'],
                                       chains['PATTERN.BIN'][1:])):
        raise ValueError('PATTERN.BIN is not fragmented')
    return volume, layout, chains


def _container_header(profile, payload_bytes):
    c = profile['container']
    d = profile['device']
    header = bytearray(c['header_bytes'])
    if c['format'] == 'anex86-hdi':
        struct.pack_into('<8I', header, 0, 0, 0, 4096, payload_bytes,
                         d['block_bytes'], d['blocks_per_track'], d['heads'],
                         d['cylinders'])
    elif c['format'] == 'virtual98-vhd1':
        header[:8] = b'VHD1.00\0'
        struct.pack_into('<HHBBHI', header, 140,
                         payload_bytes // (1024 * 1024), d['block_bytes'],
                         d['blocks_per_track'], d['heads'], d['cylinders'],
                         d['block_count'])
    return header


def build(profile):
    """Build one byte-exact fixture and a reproducible artifact record."""
    validate_profile(profile)
    files = expected_files()
    volume, layout, chains = _build_volume(profile, files)
    d, v = profile['device'], profile['volume']
    payload_bytes = d['block_count'] * d['block_bytes']
    payload = bytearray(payload_bytes)
    volume_offset = v['volume_start_device_blocks'] * d['block_bytes']
    if volume_offset + len(volume) > len(payload):
        raise ValueError('volume exceeds device payload')
    payload[volume_offset:volume_offset + len(volume)] = volume

    if v['partition_scheme'] == 'mbr-primary':
        start = v['partition_start_logical_sectors']
        end = start + v['partition_length_logical_sectors'] - 1
        mbr = memoryview(payload)[:512]
        mbr[:4] = b'\xfa\xf4\xeb\xfd'
        spt, heads = v['bpb_sectors_per_track'], v['bpb_heads']
        entry = 446
        struct.pack_into('<B3sB3sII', mbr, entry, 0, _chs(start, spt, heads),
                         v['partition_type_code'], _chs(end, spt, heads),
                         start, v['partition_length_logical_sectors'])
        mbr[510:512] = b'\x55\xaa'

    header = _container_header(profile, payload_bytes)
    image = bytes(header + payload)
    file_records = {}
    for name, content in sorted(files.items()):
        file_records[name] = {
            'size_bytes': len(content),
            'sha256': hashlib.sha256(content).hexdigest(),
            'cluster_chain': chains[name],
        }
    record = {
        'profile': profile['name'],
        'file': profile['name'] + '.' + profile['container']['file_extension'],
        'size_bytes': len(image),
        'sha256': hashlib.sha256(image).hexdigest(),
        'container_format': profile['container']['format'],
        'container_header_bytes': len(header),
        'payload_bytes': len(payload),
        'device_block_bytes': d['block_bytes'],
        'device_block_count': d['block_count'],
        'volume_offset_bytes': len(header) + volume_offset,
        'volume_start_device_blocks': v['volume_start_device_blocks'],
        'volume_sector_bytes': v['logical_sector_bytes'],
        'volume_sector_count': v['total_logical_sectors'],
        'partition_scheme': v['partition_scheme'],
        'partition_start_logical_sectors': v['partition_start_logical_sectors'],
        'partition_length_logical_sectors': v['partition_length_logical_sectors'],
        'fat_bits': v['fat_bits'],
        'fat_sectors_per_copy': layout['fat_sectors'],
        'cluster_count': layout['cluster_count'],
        'files': file_records,
    }
    return image, record


def produce(profiles_path, output):
    profiles = load(profiles_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for profile in profiles:
        image, record = build(profile)
        target = output / record['file']
        target.write_bytes(image)
        records.append(record)
    manifest = {'schema_version': 2, 'contract_id': 'pc88va-storage-m17-v1',
                'fixtures': records}
    (output / 'manifest.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    produce(args.profiles, args.output)


if __name__ == '__main__':
    main()
