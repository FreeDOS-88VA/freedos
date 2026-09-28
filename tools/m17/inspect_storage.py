#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent, read-only inspector for M17 container/FAT fixture images.

Exit status is 0 for valid-supported, 2 for recognized valid-but-unsupported
media, 3 for malformed/truncated/inconsistent input, and 64 for CLI misuse.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from contracts import (ContractError, UnsupportedProfileError, fat_layout,
                       load, validate_profile)


class MediaError(ValueError):
    """Invalid fixture/media input."""


class MalformedMediaError(MediaError):
    """Required recognizable structure or signature is absent/invalid."""


class TruncatedMediaError(MalformedMediaError):
    """A recognized media container ends before its declared extent."""


class InconsistentMediaError(MediaError):
    """Redundant fields or structures disagree or violate their extent."""


class UnsupportedMediaError(MediaError):
    """Recognized, structurally valid format outside the M17 subset."""


class UsageErrorParser(argparse.ArgumentParser):
    """Use the documented sysexits-style CLI usage status."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(64, f'{self.prog}: error: {message}\n')


EXPECTED_FILES = {
    'README.TXT': (82, '23cbc5d0a77fa91745197ac61baa735d077e45860f961b3f88e12c4c83ceb3d7'),
    'PATTERN.BIN': (70123, '03c7740d7c473e418286cd6312ad6ea47752e4485d219ffa445c150c950c250e'),
    'CROSS.BIN': (4097, '81f14fb5d606b432ede5dc980f998dbdd90d6a4480978d4160441c5675686e44'),
    'LAST.BIN': (1560, 'a99fa5db8ef031d144007962af69c820a93f891c7df27b6d0f491d1d4031337e'),
    'SUBDIR/INNER.TXT': (321, '85c102bf1f614991ee60c0ee1f2a34539327db3ccefd85ec67262d60f6e2ff7f'),
}
MANIFEST_FIELDS = {
    'profile', 'file', 'size_bytes', 'sha256', 'container_format',
    'container_header_bytes', 'payload_bytes', 'device_block_bytes',
    'device_block_count', 'volume_offset_bytes', 'volume_start_device_blocks',
    'volume_sector_bytes', 'volume_sector_count', 'partition_scheme',
    'partition_start_logical_sectors', 'partition_length_logical_sectors',
    'fat_bits', 'fat_sectors_per_copy', 'cluster_count', 'files',
}


def _need(condition, message, error=InconsistentMediaError):
    if not condition:
        raise error(message)


def _u16(data, offset):
    return int.from_bytes(data[offset:offset + 2], 'little')


def _u32(data, offset):
    return int.from_bytes(data[offset:offset + 4], 'little')


def _chs_for_lba(lba, sectors_per_track, heads):
    cylinder, remainder = divmod(lba, sectors_per_track * heads)
    head, sector0 = divmod(remainder, sectors_per_track)
    if cylinder > 1023:
        return b'\xff\xff\xff'
    return bytes((cylinder & 0xff, ((cylinder >> 2) & 0xc0) | head,
                  sector0 + 1))


def _validate_container(data, profile):
    c = profile['container']
    d = profile['device']
    payload_bytes = d['block_count'] * d['block_bytes']
    header_bytes = c['header_bytes']
    expected_size = header_bytes + payload_bytes
    if len(data) < expected_size:
        raise TruncatedMediaError('container is truncated before its declared payload end')
    _need(len(data) == expected_size, 'container has trailing or undeclared bytes')
    header = data[:header_bytes]
    if c['format'] == 'raw':
        payload = data
    elif c['format'] == 'anex86-hdi':
        if len(header) != 4096:
            raise TruncatedMediaError('HDI header is truncated')
        values = struct.unpack_from('<8I', header, 0)
        expected = (0, 0, 4096, payload_bytes, d['block_bytes'],
                    d['blocks_per_track'], d['heads'], d['cylinders'])
        _need(values == expected, 'HDI header geometry/capacity mismatch')
        _need(header[32:] == bytes(4096 - 32), 'HDI reserved header bytes are nonzero')
        payload = data[4096:]
    elif c['format'] == 'virtual98-vhd1':
        _need(header[:8] == b'VHD1.00\0', 'unrecognized VHD signature', MalformedMediaError)
        actual = struct.unpack_from('<HHBBHI', header, 140)
        expected = (payload_bytes // (1024 * 1024), d['block_bytes'],
                    d['blocks_per_track'], d['heads'], d['cylinders'],
                    d['block_count'])
        _need(actual == expected, 'VHD header geometry/capacity mismatch')
        _need(header[8:140] == bytes(132) and header[152:] == bytes(68),
              'VHD reserved header bytes are nonzero')
        payload = data[220:]
    else:
        raise UnsupportedMediaError('recognized container is outside M17 support')
    return header, payload


def _partition_offset(payload, profile):
    v = profile['volume']
    d = profile['device']
    if v['partition_scheme'] != 'mbr-primary':
        return v['volume_start_device_blocks'] * d['block_bytes']

    _need(len(payload) >= 512, 'truncated MBR', TruncatedMediaError)
    mbr = payload[:512]
    _need(mbr[510:512] == b'\x55\xaa', 'MBR signature is missing', MalformedMediaError)
    entries = [mbr[446 + 16 * i:462 + 16 * i] for i in range(4)]
    _need(all(entry == bytes(16) for entry in entries if entry[4] == 0),
          'empty MBR entry contains nonzero metadata')
    nonempty = [entry for entry in entries if entry[4] != 0]
    _need(len(nonempty) >= 1, 'MBR has no primary data partition', MalformedMediaError)
    _need(mbr[:4] == b'\xfa\xf4\xeb\xfd' and mbr[4:446] == bytes(442),
          'MBR bootstrap is not the fixed nonbootable stub')
    disk_sectors = len(payload) // 512
    spt, heads = v['bpb_sectors_per_track'], v['bpb_heads']
    ranges = []
    active_count = 0
    for entry in nonempty:
        _need(entry[0] in (0, 0x80), 'invalid MBR boot indicator')
        active_count += entry[0] == 0x80
        start = int.from_bytes(entry[8:12], 'little')
        count = int.from_bytes(entry[12:16], 'little')
        _need(start > 0 and count > 0 and start + count <= disk_sectors,
              'MBR partition is empty or outside the device')
        _need(entry[1:4] == _chs_for_lba(start, spt, heads) and
              entry[5:8] == _chs_for_lba(start + count - 1, spt, heads),
              'MBR CHS and LBA fields disagree under the selected 512-byte geometry')
        ranges.append((start, start + count))
    _need(active_count <= 1, 'multiple MBR partitions are marked active')
    for index, (start, end) in enumerate(ranges):
        _need(all(end <= other_start or other_end <= start
                  for other_start, other_end in ranges[index + 1:]),
              'MBR primary partitions overlap')
    if len(nonempty) > 1:
        raise UnsupportedMediaError('multiple primary partitions are valid but outside M17')

    entry = nonempty[0]
    _need(entries[0] == entry, 'M17 primary partition must use MBR entry zero')
    if entry[0] == 0x80:
        raise UnsupportedMediaError('active SCSI partitions are excluded')
    partition_type = entry[4]
    start = int.from_bytes(entry[8:12], 'little')
    count = int.from_bytes(entry[12:16], 'little')
    if partition_type != 0x06:
        raise UnsupportedMediaError('valid primary partition type is outside M17 FAT16 type 06h')
    expected_start = v['partition_start_logical_sectors']
    expected_count = v['partition_length_logical_sectors']
    _need((start, count) == (expected_start, expected_count),
          'MBR LBA start/length disagree with the selected profile')
    logical_offset = start * 512
    device_offset = v['volume_start_device_blocks'] * d['block_bytes']
    _need(logical_offset == device_offset,
          'MBR 512-byte LBA and device-block volume offsets disagree')
    return logical_offset


def _volume_geometry(data, volume_offset, profile):
    v = profile['volume']
    d = profile['device']
    bps = v['logical_sector_bytes']
    volume_bytes = v['total_logical_sectors'] * bps
    _need(volume_offset + volume_bytes <= len(data),
          'BPB volume extends beyond device payload')
    boot = data[volume_offset:volume_offset + bps]
    _need(len(boot) == bps, 'truncated BPB sector', TruncatedMediaError)
    actual_bps = _u16(boot, 11)
    if actual_bps not in (128, 256, 512, 1024, 2048, 4096):
        raise MalformedMediaError('BPB has an invalid logical sector length')
    if actual_bps not in (512, 1024):
        raise UnsupportedMediaError('recognized FAT volume has unsupported logical sector length')
    total_small = _u16(boot, 19)
    total_large = _u32(boot, 32)
    _need(not (total_small and total_large), 'BPB small/large total-sector fields conflict')
    actual_total = total_small or total_large
    actual_fat = _u16(boot, 22)
    _need(boot[:3] == b'\xeb\x3c\x90' and boot[3:11] == b'PC88VA17',
          'BPB jump/OEM identity mismatch')
    _need(boot[510:512] == b'\x55\xaa', 'BPB signature is missing', MalformedMediaError)
    _need(boot[62:66] == b'\xfa\xf4\xeb\xfd',
          'volume boot code is not the fixed nonbootable stub')
    _need((
        _u16(boot, 11), boot[13], _u16(boot, 14), boot[16], _u16(boot, 17),
        boot[21], actual_fat, _u16(boot, 24), _u16(boot, 26), _u32(boot, 28),
        actual_total, boot[38], _u32(boot, 39), boot[43:54], boot[54:62]
    ) == (
        bps, v['sectors_per_cluster'], v['reserved_sectors'], v['fat_count'],
        v['root_entries'], v['media_descriptor'], actual_fat,
        v['bpb_sectors_per_track'], v['bpb_heads'], v['hidden_sectors'],
        v['total_logical_sectors'], 0x29, v['volume_serial'],
        v['volume_label'].ljust(11).encode('ascii'),
        ('FAT%d' % v['fat_bits']).ljust(8).encode('ascii')
    ), 'BPB geometry/identity mismatch')
    if (actual_total <= 0xffff):
        _need(total_small == actual_total and total_large == 0,
              'BPB small/large total-sector encoding is not canonical')
    else:
        _need(total_small == 0 and total_large == actual_total,
              'BPB large total-sector encoding is not canonical')
    if _u16(boot, 11) != bps:
        raise UnsupportedMediaError('FAT volume uses an unsupported BPB sector size')
    layout = fat_layout(profile)
    _need(actual_fat == layout['fat_sectors'], 'BPB FAT size is inconsistent with the profile')
    _need(4 <= layout['cluster_count'] <= 65524,
          'cluster count outside FAT12/FAT16 range', UnsupportedMediaError)
    return layout, volume_bytes


def _fat_value(fat, bits, cluster):
    if bits == 16:
        offset = cluster * 2
        if offset + 2 > len(fat):
            raise InconsistentMediaError('FAT16 entry exceeds FAT extent')
        return int.from_bytes(fat[offset:offset + 2], 'little')
    offset = cluster + cluster // 2
    if offset + 2 > len(fat):
        raise InconsistentMediaError('FAT12 entry exceeds FAT extent')
    pair = int.from_bytes(fat[offset:offset + 2], 'little')
    return (pair >> 4 if cluster & 1 else pair) & 0x0fff


def _read_files(payload, volume_offset, profile, layout, volume_bytes):
    v = profile['volume']
    bps, spc, bits = v['logical_sector_bytes'], v['sectors_per_cluster'], v['fat_bits']
    fat_bytes = layout['fat_sectors'] * bps
    fat_offset = volume_offset + v['reserved_sectors'] * bps
    _need(fat_offset + 2 * fat_bytes <= volume_offset + volume_bytes,
          'FAT copies extend beyond volume')
    fat = payload[fat_offset:fat_offset + fat_bytes]
    second_fat = payload[fat_offset + fat_bytes:fat_offset + 2 * fat_bytes]
    _need(fat == second_fat, 'FAT mirrors differ')
    mask = (1 << bits) - 1
    eoc_min = mask - 7
    _need(_fat_value(fat, bits, 0) == ((mask & ~0xff) | v['media_descriptor']) and
          _fat_value(fat, bits, 1) >= eoc_min,
          'FAT reserved entries are invalid')
    root_offset = (fat_offset + 2 * fat_bytes)
    root_bytes = layout['root_sectors'] * bps
    root = payload[root_offset:root_offset + root_bytes]
    _need(len(root) == root_bytes, 'truncated root directory', TruncatedMediaError)
    data_offset = volume_offset + layout['data_start_sector'] * bps
    cluster_bytes = spc * bps
    cluster_limit = layout['cluster_count'] + 2
    owned = set()

    def chain(first):
        result = bytearray()
        chain_clusters = []
        current = first
        for _ in range(layout['cluster_count']):
            _need(2 <= current < cluster_limit, 'FAT chain points outside data clusters')
            _need(current not in owned, 'FAT loop or cross-linked cluster')
            owned.add(current)
            chain_clusters.append(current)
            offset = data_offset + (current - 2) * cluster_bytes
            _need(offset + cluster_bytes <= volume_offset + volume_bytes,
                  'cluster data extent exceeds volume')
            result.extend(payload[offset:offset + cluster_bytes])
            next_cluster = _fat_value(fat, bits, current)
            if next_cluster >= eoc_min:
                return bytes(result), chain_clusters
            _need(next_cluster not in (0, 1, mask - 8),
                  'FAT chain terminates at a free/reserved/bad cluster')
            current = next_cluster
        raise InconsistentMediaError('FAT chain exceeds data-cluster limit')

    found = {}
    root_names = set()
    last_chain = []

    def parse_directory(entries, prefix='', self_cluster=0, parent_cluster=0):
        nonlocal last_chain
        terminated = False
        for offset in range(0, len(entries), 32):
            entry = entries[offset:offset + 32]
            _need(len(entry) == 32, 'partial directory entry')
            if entry[0] == 0:
                terminated = True
                _need(entries[offset:] == bytes(len(entries) - offset),
                      'nonzero directory bytes follow end marker')
                break
            _need(entry[0] != 0xe5, 'deleted directory entry outside fixture contract',
                  UnsupportedMediaError)
            _need(entry[11] != 0x0f, 'long-filename entries are outside the M17 fixture subset',
                  UnsupportedMediaError)
            try:
                stem = entry[:8].decode('ascii', errors='strict').rstrip()
                extension = entry[8:11].decode('ascii', errors='strict').rstrip()
            except UnicodeDecodeError as error:
                raise MalformedMediaError('directory name is not selected ASCII 8.3') from error
            name = stem + ('.' + extension if extension else '')
            first = int.from_bytes(entry[26:28], 'little')
            size = int.from_bytes(entry[28:32], 'little')
            attr = entry[11]
            if name in ('.', '..'):
                _need(prefix and attr == 0x10 and
                      first == (self_cluster if name == '.' else parent_cluster),
                      'subdirectory dot entries are inconsistent')
                continue
            if attr == 0x08:
                _need(not prefix and name == v['volume_label'] and first == 0 and size == 0,
                      'root volume-label entry is inconsistent')
                continue
            path = prefix + name
            _need(path not in root_names, 'duplicate directory entry')
            root_names.add(path)
            content, allocated = chain(first)
            if attr == 0x10:
                _need(not prefix and name == 'SUBDIR' and size == 0,
                      'unexpected directory entry', UnsupportedMediaError)
                _need(len(content) >= 96 and content[:11] == b'.          ' and
                      content[32:43] == b'..         ',
                      'subdirectory dot entries missing')
                parse_directory(content, 'SUBDIR/', first, 0)
            else:
                if attr != 0x20:
                    raise UnsupportedMediaError('unsupported directory attribute')
                _need(0 < size <= len(content),
                      'file size exceeds its allocated FAT chain')
                expected_clusters = (size + cluster_bytes - 1) // cluster_bytes
                _need(len(allocated) == expected_clusters,
                      'file size and FAT chain length disagree')
                _need(content[size:] == bytes(len(content) - size),
                      'nonzero bytes follow file end within cluster chain')
                found[path] = (content[:size], allocated)
                if path == 'LAST.BIN':
                    last_chain = allocated
        _need(terminated, 'directory lacks a zero end marker')

    _need(root[:11] == v['volume_label'].ljust(11).encode('ascii') and root[11] == 0x08,
          'root volume label is missing or malformed')
    parse_directory(root)
    expected_names = set(EXPECTED_FILES)
    _need(set(found) == expected_names, 'fixture file set differs from independent golden set')
    for name, (expected_size, expected_hash) in EXPECTED_FILES.items():
        content, _ = found[name]
        _need(len(content) == expected_size and
              hashlib.sha256(content).hexdigest() == expected_hash,
              'independent file payload hash mismatch: ' + name)
    _need(last_chain and max(last_chain) == layout['cluster_count'] + 1,
          'LAST.BIN does not exercise the last data cluster')
    pattern_chain = found['PATTERN.BIN'][1]
    _need(len(pattern_chain) > 1 and
          any(right != left + 1 for left, right in zip(pattern_chain, pattern_chain[1:])),
          'PATTERN.BIN is not fragmented across clusters')
    allocated = {cluster for cluster in range(2, cluster_limit)
                 if _fat_value(fat, bits, cluster) != 0}
    _need(allocated == owned, 'orphan or unreferenced FAT allocation')
    for cluster in range(cluster_limit, (len(fat) * 8 // bits)):
        if bits == 16:
            value = _fat_value(fat, bits, cluster)
        else:
            offset = cluster + cluster // 2
            if offset + 2 > len(fat):
                break
            value = _fat_value(fat, bits, cluster)
        _need(value == 0, 'FAT allocates clusters beyond volume data area')

    return {
        'files': {
            name: {'size_bytes': len(content),
                   'sha256': hashlib.sha256(content).hexdigest(),
                   'cluster_chain': clusters}
            for name, (content, clusters) in sorted(found.items())
        },
        'fat_sectors_per_copy': layout['fat_sectors'],
        'cluster_count': layout['cluster_count'],
    }


def inspect(data, profile):
    """Inspect one fixture; never writes to or normalizes the supplied bytes."""
    try:
        validate_profile(profile)
    except UnsupportedProfileError as error:
        raise UnsupportedMediaError(str(error)) from error
    except ContractError as error:
        raise InconsistentMediaError('invalid profile contract: ' + str(error)) from error
    header, payload = _validate_container(data, profile)
    d, v = profile['device'], profile['volume']
    if d['transport'] == 'sasi':
        prefix_bytes = v['native_boot_reserved_device_blocks'] * d['block_bytes']
        _need(payload[:prefix_bytes] == bytes(prefix_bytes),
              'SASI native boot reservation is not preserved as a zeroed nonbootable prefix')
    volume_offset = _partition_offset(payload, profile)
    expected_device_offset = v['volume_start_device_blocks'] * d['block_bytes']
    _need(volume_offset == expected_device_offset,
          'partition and native device-block volume offsets disagree')
    layout, volume_bytes = _volume_geometry(payload, volume_offset, profile)
    file_info = _read_files(payload, volume_offset, profile, layout, volume_bytes)
    return {
        'profile': profile['name'],
        'container_format': profile['container']['format'],
        'container_header_bytes': len(header),
        'payload_bytes': len(payload),
        'volume_offset_bytes': len(header) + volume_offset,
        'volume_sector_bytes': v['logical_sector_bytes'],
        'volume_sector_count': v['total_logical_sectors'],
        'partition_scheme': v['partition_scheme'],
        'partition_start_logical_sectors': v['partition_start_logical_sectors'],
        'partition_length_logical_sectors': v['partition_length_logical_sectors'],
        'fat_bits': v['fat_bits'],
        **file_info,
    }


def _manifest_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InconsistentMediaError('duplicate manifest key: ' + key)
        result[key] = value
    return result


def _verify_manifest(directory, profiles):
    manifest_path = directory / 'manifest.json'
    _need(not manifest_path.is_symlink() and
          manifest_path.parent.resolve() == directory.resolve(),
          'manifest path escapes media directory or is a symlink')
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'),
                              object_pairs_hook=_manifest_object)
    except (OSError, json.JSONDecodeError) as error:
        raise InconsistentMediaError(f'cannot read fixture manifest: {error}') from error
    _need(isinstance(manifest, dict) and
          set(manifest) == {'schema_version', 'contract_id', 'fixtures'} and
          type(manifest['schema_version']) is int and manifest['schema_version'] == 2 and
          manifest['contract_id'] == 'pc88va-storage-m17-v1',
          'fixture manifest schema/contract mismatch')
    rows = manifest['fixtures']
    _need(isinstance(rows, list) and len(rows) == len(profiles),
          'fixture manifest profile count mismatch')
    results = []
    for profile, row in zip(profiles, rows):
        _need(isinstance(row, dict) and set(row) == MANIFEST_FIELDS,
              'fixture manifest row has unknown or missing fields')
        extension = profile['container']['file_extension']
        filename = profile['name'] + '.' + extension
        _need(row['profile'] == profile['name'] and row['file'] == filename,
              'manifest profile/file identity mismatch')
        path = directory / filename
        _need(path.parent.resolve() == directory.resolve() and not path.is_symlink(),
              'fixture path escapes media directory or is a symlink')
        try:
            data = path.read_bytes()
        except OSError as error:
            raise TruncatedMediaError(f'cannot read fixture {filename}: {error}') from error
        digest = hashlib.sha256(data).hexdigest()
        _need(type(row['size_bytes']) is int and row['size_bytes'] == len(data) and
              row['sha256'] == digest,
              'fixture manifest size/hash mismatch')
        actual = inspect(data, profile)
        expected_fields = {
            'container_format': actual['container_format'],
            'container_header_bytes': actual['container_header_bytes'],
            'payload_bytes': actual['payload_bytes'],
            'device_block_bytes': profile['device']['block_bytes'],
            'device_block_count': profile['device']['block_count'],
            'volume_offset_bytes': actual['volume_offset_bytes'],
            'volume_start_device_blocks': profile['volume']['volume_start_device_blocks'],
            'volume_sector_bytes': actual['volume_sector_bytes'],
            'volume_sector_count': actual['volume_sector_count'],
            'partition_scheme': actual['partition_scheme'],
            'partition_start_logical_sectors': actual['partition_start_logical_sectors'],
            'partition_length_logical_sectors': actual['partition_length_logical_sectors'],
            'fat_bits': actual['fat_bits'],
            'fat_sectors_per_copy': actual['fat_sectors_per_copy'],
            'cluster_count': actual['cluster_count'],
            'files': actual['files'],
        }
        _need(all(row[key] == value for key, value in expected_fields.items()),
              'fixture manifest semantics differ from independent inspection')
        results.append(actual)
    return results


def main(argv=None):
    parser = UsageErrorParser(description=__doc__)
    parser.add_argument('--profiles', type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--directory', type=Path)
    group.add_argument('--input', type=Path)
    parser.add_argument('--profile', help='profile name required with --input')
    args = parser.parse_args(argv)
    if (args.input is not None) != (args.profile is not None):
        parser.error('--input and --profile must be used together')
    try:
        profiles = load(args.profiles)
        if args.directory is not None:
            results = _verify_manifest(args.directory, profiles)
        else:
            by_name = {profile['name']: profile for profile in profiles}
            if args.profile not in by_name:
                parser.error('--profile must name one of the selected M17 profiles')
            results = [inspect(args.input.read_bytes(), by_name[args.profile])]
        print(json.dumps({'classification': 'valid-supported', 'fixtures': results},
                         sort_keys=True))
        return 0
    except UnsupportedMediaError as error:
        print(f'valid-but-unsupported: {error}', file=sys.stderr)
        return 2
    except TruncatedMediaError as error:
        print(f'malformed/truncated: {error}', file=sys.stderr)
        return 3
    except MalformedMediaError as error:
        print(f'malformed: {error}', file=sys.stderr)
        return 3
    except InconsistentMediaError as error:
        print(f'inconsistent: {error}', file=sys.stderr)
        return 3
    except (MediaError, ContractError, OSError) as error:
        print(f'invalid input: {error}', file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
