#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Produce public, nonbootable FAT fixtures without DOS or firmware inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from contracts import load, validate


def build(p):
    validate(p)
    bps = p['logical_sector_bytes']
    spc = p['sectors_per_cluster']
    bits = p['fat_bits']
    capacity = p['cylinders'] * p['heads'] * p['sectors_per_track'] * p['physical_sector_bytes']
    start = p['partition_start']
    total = capacity // bps - start
    rootsecs = p['root_entries'] * 32 // bps
    # Pick the smallest FAT that can describe the resulting data area.
    fatsecs = 1
    while True:
        clusters = (total - 1 - 2 * fatsecs - rootsecs) // spc
        need = ((clusters + 2) * bits + 7) // 8
        if need <= fatsecs * bps:
            break
        fatsecs += 1
    if not (4 <= clusters < 4085 if bits == 12 else 4085 <= clusters < 65525):
        raise ValueError('cluster count does not match selected FAT type')
    volume = bytearray(total * bps)
    boot = memoryview(volume)[:bps]
    boot[:11] = b'\xeb\x3c\x90VA17DATA'
    struct.pack_into('<HBHBHHBHHHII', boot, 11, bps, spc, 1, 2,
                     p['root_entries'], total if total < 65536 else 0,
                     p['media_descriptor'], fatsecs, p['sectors_per_track'],
                     p['heads'], start, total if total >= 65536 else 0)
    boot[36] = 0x80 if p['container'] != 'raw' else 0
    boot[38] = 0x29
    struct.pack_into('<I', boot, 39, p['volume_serial'])
    boot[43:54] = p['volume_label'].ljust(11).encode()
    boot[54:62] = f'FAT{bits}'.ljust(8).encode()
    # Halt if mistakenly executed; fixtures provide no native boot service.
    boot[62:66] = b'\xfa\xf4\xeb\xfd'
    boot[510:512] = b'\x55\xaa'
    fat = bytearray(fatsecs * bps)
    def setfat(n, value):
        if bits == 16:
            struct.pack_into('<H', fat, n * 2, value)
        else:
            off = n * 3 // 2
            pair = int.from_bytes(fat[off:off + 2], 'little')
            pair = (pair & 0x000f | value << 4) if n & 1 else (pair & 0xf000 | value)
            fat[off:off + 2] = pair.to_bytes(2, 'little')
    eoc = (1 << bits) - 1
    setfat(0, (eoc & ~255) | p['media_descriptor'])
    setfat(1, eoc)
    dataoff = (1 + 2 * fatsecs + rootsecs) * bps
    cb = spc * bps
    root = bytearray(rootsecs * bps)
    def entry(name, attr, cluster, size):
        e = bytearray(32)
        if name in ('.', '..'):
            encoded = name.ljust(11)
        else:
            stem, _, ext = name.partition('.')
            encoded = stem.ljust(8) + ext.ljust(3)
        e[:11] = encoded.encode()
        e[11] = attr
        # 2026-01-01 00:00:00, fixed public build timestamp.
        struct.pack_into('<HHHI', e, 22, 0, (46 << 9) | (1 << 5) | 1, cluster, size)
        return e
    def put(chain, payload):
        for i, cluster in enumerate(chain):
            setfat(cluster, chain[i + 1] if i + 1 < len(chain) else eoc)
            chunk = payload[i * cb:(i + 1) * cb]
            off = dataoff + (cluster - 2) * cb
            volume[off:off + len(chunk)] = chunk
    files = {'README.TXT': b'Public M17 storage fixture. Data only; guest support is not implied.\r\n',
             'PATTERN.BIN': bytes(range(256)) * 128 + b'end',
             'LAST.BIN': b'Last allocatable cluster\r\n' + bytes(range(256)) * 2,
             'SUBDIR/INNER.TXT': b'Nested directory readback.\r\n'}
    root[:32] = p['volume_label'].ljust(11).encode() + b'\x08' + bytes(20)
    # Fragment PATTERN.BIN intentionally and put LAST.BIN at the volume end.
    nextcl = 2
    used = set()
    def allocate(size):
        nonlocal nextcl
        chain = []
        for _ in range((size + cb - 1) // cb):
            while nextcl in used:
                nextcl += 1
            chain.append(nextcl)
            used.add(nextcl)
            nextcl += 2
        return chain
    for index, name in enumerate(('README.TXT', 'PATTERN.BIN', 'LAST.BIN'), 1):
        content = files[name]
        count = (len(content) + cb - 1) // cb
        chain = list(range(clusters + 2 - count, clusters + 2)) if name == 'LAST.BIN' else allocate(len(content))
        if name == 'LAST.BIN':
            if used.intersection(chain):
                raise ValueError('fixture files exceed data capacity')
            used.update(chain)
        put(chain, content)
        root[index * 32:(index + 1) * 32] = entry(name, 0x20, chain[0], len(content))
    directory = allocate(cb)[0]
    inner = allocate(len(files['SUBDIR/INNER.TXT']))
    put(inner, files['SUBDIR/INNER.TXT'])
    entries = entry('.', 0x10, directory, 0) + entry('..', 0x10, 0, 0) + entry('INNER.TXT', 0x20, inner[0], len(files['SUBDIR/INNER.TXT']))
    put([directory], entries)
    root[128:160] = entry('SUBDIR', 0x10, directory, 0)
    volume[bps:bps + len(fat)] = fat
    volume[bps + len(fat):bps + 2 * len(fat)] = fat
    rootoff = (1 + 2 * fatsecs) * bps
    volume[rootoff:rootoff + len(root)] = root
    disk = bytearray(capacity)
    disk[start * bps:] = volume
    if start:
        disk[:4] = b'\xfa\xf4\xeb\xfd'
        # Nonbootable primary FAT16 volume. CHS is deliberately saturated;
        # consumers must use checked LBA/count fields for this profile.
        struct.pack_into('<B3sB3sII', disk, 446, 0, b'\xfe\xff\xff', 6,
                         b'\xfe\xff\xff', start, total)
        disk[510:512] = b'\x55\xaa'
    header = bytearray()
    if p['container'] == 'hdi':
        header = bytearray(4096)
        struct.pack_into('<8I', header, 0, 0, 0, 4096, capacity,
                         p['physical_sector_bytes'], p['sectors_per_track'], p['heads'], p['cylinders'])
    elif p['container'] == 'vhd':
        header = bytearray(220)
        header[:8] = b'VHD1.00\0'
        struct.pack_into('<HHBBHI', header, 140, capacity // 1048576,
                         p['physical_sector_bytes'], p['sectors_per_track'], p['heads'],
                         p['cylinders'], capacity // p['physical_sector_bytes'])
    image = bytes(header + disk)
    record = {'name': p['name'], 'size': len(image), 'sha256': hashlib.sha256(image).hexdigest(),
              'container_header_bytes': len(header), 'volume_offset_bytes': len(header) + start * bps,
              'volume_sectors': total, 'fat_sectors': fatsecs, 'clusters': clusters,
              'files': {n: {'size': len(v), 'sha256': hashlib.sha256(v).hexdigest()} for n, v in files.items()}}
    return image, record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--profiles', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    profiles = load(args.profiles)
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    for p in profiles:
        image, record = build(p)
        ext = {'raw': 'img', 'hdi': 'hdi', 'vhd': 'hdd'}[p['container']]
        record['file'] = p['name'] + '.' + ext
        (args.output / record['file']).write_bytes(image)
        records.append(record)
    (args.output / 'manifest.json').write_text(json.dumps({'schema_version': 1, 'fixtures': records}, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
