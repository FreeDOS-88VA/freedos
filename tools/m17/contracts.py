# SPDX-License-Identifier: GPL-2.0-or-later
"""Versioned M17 media contract and checked unit-conversion helpers.

This module validates metadata only.  It does not claim DOS, emulator, or
hardware support for any generated fixture.
"""
import json
import re
from pathlib import Path


class ContractError(ValueError):
    """Malformed or internally inconsistent profile/fixture input."""


class UnsupportedProfileError(ContractError):
    """Recognized storage shape outside the deliberately small M17 set."""


class RangeError(ContractError):
    """Invalid or out-of-range LBA/count conversion."""


ROOT_FIELDS = {'schema_version', 'contract_id', 'evidence', 'profiles'}
PROFILE_FIELDS = {'name', 'container', 'deployment', 'device', 'volume',
                  'qualification', 'evidence_refs'}
CONTAINER_FIELDS = {'format', 'header_bytes', 'payload_offset_bytes',
                    'file_extension'}
DEPLOYMENT_FIELDS = {'kind', 'controller_owner', 'firmware_interface',
                     'driver_filename', 'load_method', 'permitted_boot_sources',
                     'bootable_fixture'}
DEVICE_FIELDS = {'transport', 'controller_model', 'native_unit', 'target_id',
                 'lun', 'block_bytes', 'block_count', 'cylinders', 'heads',
                 'blocks_per_track'}
VOLUME_FIELDS = {'partition_scheme', 'volume_start_device_blocks',
                 'native_boot_reserved_device_blocks',
                 'partition_start_logical_sectors',
                 'partition_length_logical_sectors', 'partition_type_code',
                 'partition_entries', 'partition_boot_indicator',
                 'logical_sector_bytes', 'bpb_sectors_per_track', 'bpb_heads',
                 'total_logical_sectors', 'hidden_sectors', 'reserved_sectors',
                 'fat_count', 'fat_bits', 'sectors_per_cluster', 'root_entries',
                 'media_descriptor',
                 'volume_serial', 'volume_label'}
QUALIFICATION_FIELDS = {'m17', 'guest', 'hardware',
                        'planned_data_milestone', 'planned_boot_milestone',
                        'planned_write_milestone'}
EXPECTED_PROFILES = {
    'fdd-360-fat12', 'fdd-1280-fat12', 'sasi40-fat12', 'sasi40-fat16',
    'scsi40-256-fat16', 'scsi40-512-fat16',
}
HEX40 = re.compile(r'^[0-9a-f]{40}$')


def _object(value, fields, label):
    if not isinstance(value, dict) or set(value) != fields:
        raise ContractError(f'{label}: unknown or missing fields')


def _int(value, label, low=None, high=None):
    if type(value) is not int:
        raise ContractError(f'{label}: integer required')
    if low is not None and value < low:
        raise ContractError(f'{label}: below minimum')
    if high is not None and value > high:
        raise ContractError(f'{label}: above maximum')
    return value


def _text(value, label, pattern=None):
    if not isinstance(value, str) or not value:
        raise ContractError(f'{label}: nonempty string required')
    if pattern and not re.fullmatch(pattern, value):
        raise ContractError(f'{label}: invalid syntax')
    return value


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def validate_evidence(evidence):
    if not isinstance(evidence, dict) or not evidence:
        raise ContractError('evidence must be a nonempty object')
    for name, item in evidence.items():
        _text(name, 'evidence id', r'[a-z0-9-]{1,48}')
        if not isinstance(item, dict) or 'kind' not in item:
            raise ContractError(f'evidence {name}: missing kind')
        kind = _text(item['kind'], f'evidence {name} kind')
        if kind == 'owner-confirmed-scope':
            _object(item, {'kind', 'statement'}, f'evidence {name}')
            _text(item['statement'], f'evidence {name} statement')
            continue
        _object(item, {'kind', 'repository', 'commit', 'files'},
                f'evidence {name}')
        repo = _text(item['repository'], f'evidence {name} repository')
        if not repo.startswith('https://'):
            raise ContractError(f'evidence {name}: public HTTPS repository required')
        if not isinstance(item['commit'], str) or not HEX40.fullmatch(item['commit']):
            raise ContractError(f'evidence {name}: full lower-case commit required')
        files = item['files']
        if (not isinstance(files, list) or not files or
                any(not isinstance(filename, str) or not filename for filename in files)):
            raise ContractError(f'evidence {name}: nonempty source file list required')
        if len(set(files)) != len(files):
            raise ContractError(f'evidence {name}: duplicate file reference')
        for filename in files:
            _text(filename, f'evidence {name} filename', r'[A-Za-z0-9_./-]+')
            if filename.startswith('/') or '..' in Path(filename).parts:
                raise ContractError(f'evidence {name}: non-relative source path')


def _check_nested(p):
    _object(p, PROFILE_FIELDS, 'profile')
    _object(p['container'], CONTAINER_FIELDS, 'container')
    _object(p['deployment'], DEPLOYMENT_FIELDS, 'deployment')
    _object(p['device'], DEVICE_FIELDS, 'device')
    _object(p['volume'], VOLUME_FIELDS, 'volume')
    _object(p['qualification'], QUALIFICATION_FIELDS, 'qualification')


def fat_type_for_clusters(cluster_count):
    _int(cluster_count, 'cluster count', 1, 0xffffffff)
    if cluster_count < 4085:
        return 12
    if cluster_count < 65525:
        return 16
    return 32


def fat_layout(profile):
    """Return deterministic BPB FAT sizing for a validated profile."""
    volume = profile['volume']
    bps = volume['logical_sector_bytes']
    total = volume['total_logical_sectors']
    root_sectors = (volume['root_entries'] * 32 + bps - 1) // bps
    fat_count = volume['fat_count']
    reserved = volume['reserved_sectors']
    spc = volume['sectors_per_cluster']
    for fat_sectors in range(1, max(2, total // fat_count + 1)):
        data_sectors = total - reserved - fat_count * fat_sectors - root_sectors
        if data_sectors <= 0:
            raise ContractError('FAT metadata consumes the volume')
        clusters = data_sectors // spc
        required_bytes = ((clusters + 2) * volume['fat_bits'] + 7) // 8
        if required_bytes <= fat_sectors * bps:
            if fat_type_for_clusters(clusters) != volume['fat_bits']:
                raise ContractError('FAT type disagrees with cluster-count thresholds')
            return {
                'root_sectors': root_sectors,
                'fat_sectors': fat_sectors,
                'cluster_count': clusters,
                'data_start_sector': reserved + fat_count * fat_sectors + root_sectors,
                'cluster_bytes': spc * bps,
            }
    raise ContractError('could not size FAT within volume')


def validate_profile(p):
    _check_nested(p)
    _text(p['name'], 'profile name', r'[a-z0-9-]{1,40}')
    c, d, v, q = p['container'], p['device'], p['volume'], p['qualification']

    fmt = _text(c['format'], 'container format')
    container_shape = {
        'raw': (0, 'img'),
        'anex86-hdi': (4096, 'hdi'),
        'virtual98-vhd1': (220, 'hdd'),
    }
    if fmt not in container_shape:
        raise UnsupportedProfileError('unsupported container format')
    header_bytes, extension = container_shape[fmt]
    if (_int(c['header_bytes'], 'container header', 0) != header_bytes or
            _int(c['payload_offset_bytes'], 'payload offset', 0) != header_bytes or
            c['file_extension'] != extension):
        raise ContractError('container header/offset/extension mismatch')

    transport = _text(d['transport'], 'transport')
    if transport not in {'fdd', 'sasi', 'scsi'}:
        raise UnsupportedProfileError('unsupported transport')
    _text(d['controller_model'], 'controller model')
    for key, high in (('native_unit', 1), ('target_id', 6), ('lun', 7)):
        if d[key] is not None:
            _int(d[key], 'device ' + key, 0, high)
    block_bytes = _int(d['block_bytes'], 'device block bytes', 1, 1024)
    if block_bytes not in (256, 512, 1024):
        raise UnsupportedProfileError('device block size outside selected set')
    block_count = _int(d['block_count'], 'device block count', 1, 0x7fffffff)
    cylinders = _int(d['cylinders'], 'cylinders', 1, 65535)
    heads = _int(d['heads'], 'heads', 1, 255)
    blocks_per_track = _int(d['blocks_per_track'], 'blocks per track', 1, 255)
    if block_count != cylinders * heads * blocks_per_track:
        raise ContractError('device block capacity disagrees with geometry')
    payload_bytes = block_count * block_bytes
    if payload_bytes > 64 * 1024 * 1024:
        raise UnsupportedProfileError('payload exceeds M17 fixture bound')

    deployment = p['deployment']
    if deployment['bootable_fixture'] is not False:
        raise ContractError('M17 data fixtures must remain nonbootable')
    if not isinstance(deployment['permitted_boot_sources'], list) or not deployment['permitted_boot_sources']:
        raise ContractError('permitted boot sources must be nonempty')
    if (any(not isinstance(x, str) or not x for x in deployment['permitted_boot_sources']) or
            len(set(deployment['permitted_boot_sources'])) != len(deployment['permitted_boot_sources'])):
        raise ContractError('invalid or duplicate permitted boot source')
    if any(x.upper() == 'SCSI' for x in deployment['permitted_boot_sources']):
        raise ContractError('SCSI boot is excluded')

    if transport == 'fdd':
        if (fmt != 'raw' or deployment['kind'] != 'kernel-builtin' or
                deployment['driver_filename'] is not None or
                deployment['load_method'] != 'built-in' or
                d['native_unit'] not in (0, 1) or d['target_id'] is not None or
                d['lun'] is not None or block_bytes not in (512, 1024) or
                deployment['controller_owner'] != 'FreeDOS VA FDD adapter'):
            raise ContractError('FDD controller/deployment binding mismatch')
        if (v['partition_scheme'] != 'none' or
                v['volume_start_device_blocks'] != 0 or
                v['native_boot_reserved_device_blocks'] != 0 or
                v['partition_start_logical_sectors'] != 0 or
                v['partition_length_logical_sectors'] != 0 or
                v['partition_type_code'] is not None or
                v['partition_entries'] != 0 or v['hidden_sectors'] != 0 or
                v['logical_sector_bytes'] != block_bytes or
                v['total_logical_sectors'] != block_count):
            raise ContractError('FDD volume geometry/partition mismatch')
        if deployment['permitted_boot_sources'] != ['FDD']:
            raise ContractError('FDD profile boot-source policy mismatch')
        expected_data, expected_boot, expected_write = 'M16', None, 'M16'
    elif transport == 'sasi':
        if (fmt != 'anex86-hdi' or deployment['kind'] != 'kernel-builtin-native-sasi' or
                deployment['driver_filename'] is not None or
                deployment['load_method'] != 'built-in' or
                d['native_unit'] not in (0, 1) or d['target_id'] is not None or
                d['lun'] is not None or block_bytes != 256 or
                (cylinders, heads, blocks_per_track) != (615, 8, 33) or
                deployment['controller_owner'] != 'FreeDOS PC-88VA SASI adapter'):
            raise UnsupportedProfileError('only the evidenced initial native SASI profile is selected')
        if (v['partition_scheme'] != 'native-prefix-superfloppy' or
                v['volume_start_device_blocks'] != 4 or
                v['native_boot_reserved_device_blocks'] != 4 or
                v['partition_start_logical_sectors'] != 0 or
                v['partition_length_logical_sectors'] != 0 or
                v['partition_type_code'] is not None or
                v['partition_entries'] != 0 or v['hidden_sectors'] != 0 or
                v['logical_sector_bytes'] != 512 or
                (block_count - 4) * block_bytes % 512 or
                v['total_logical_sectors'] != (block_count - 4) * block_bytes // 512):
            raise ContractError('SASI native-prefix volume mapping mismatch')
        if deployment['permitted_boot_sources'] != ['FDD', 'SASI-after-M20']:
            raise ContractError('SASI boot-source policy mismatch')
        expected_data, expected_boot, expected_write = 'M19', 'M20', 'M19'
    else:
        if (fmt != 'virtual98-vhd1' or deployment['kind'] != 'external-dos-block-driver' or
                deployment['controller_owner'] != 'VASCSI.SYS' or
                deployment['driver_filename'] != 'VASCSI.SYS' or
                deployment['load_method'] != 'CONFIG.SYS DEVICE= from an already accessible FDD or qualified SASI volume' or
                d['native_unit'] is not None or d['target_id'] != 0 or d['lun'] != 0 or
                block_bytes not in (256, 512) or heads != 8 or blocks_per_track != 32):
            raise UnsupportedProfileError('only the initial external SCSI target 0/LUN 0 profile is selected')
        disk_sectors = payload_bytes // 512
        start = _int(v['partition_start_logical_sectors'], 'partition start', 1)
        if (v['partition_scheme'] != 'mbr-primary' or
                v['native_boot_reserved_device_blocks'] != 0 or
                v['partition_entries'] != 1 or v['partition_type_code'] != 0x06 or
                v['partition_boot_indicator'] != 0 or
                v['partition_length_logical_sectors'] != v['total_logical_sectors'] or
                v['hidden_sectors'] != start or
                start * 512 % block_bytes or
                v['volume_start_device_blocks'] != start * 512 // block_bytes or
                start + v['total_logical_sectors'] != disk_sectors):
            raise ContractError('SCSI MBR/volume capacity mapping mismatch')
        if deployment['permitted_boot_sources'] != ['FDD', 'SASI-after-M20']:
            raise ContractError('SCSI must remain data-only and load from an earlier boot source')
        expected_data, expected_boot, expected_write = 'M21', None, 'M22'

    if v['partition_scheme'] not in {'none', 'native-prefix-superfloppy', 'mbr-primary'}:
        raise UnsupportedProfileError('unsupported partition scheme')
    _int(v['volume_start_device_blocks'], 'volume start block', 0, block_count - 1)
    _int(v['native_boot_reserved_device_blocks'], 'native boot prefix', 0, block_count - 1)
    _int(v['partition_start_logical_sectors'], 'partition start', 0, 0xffffffff)
    _int(v['partition_length_logical_sectors'], 'partition length', 0, 0xffffffff)
    _int(v['partition_entries'], 'partition entries', 0, 1)
    _int(v['partition_boot_indicator'], 'partition boot indicator', 0, 0)
    bps = _int(v['logical_sector_bytes'], 'BPB bytes per sector', 512, 1024)
    if bps not in (512, 1024):
        raise UnsupportedProfileError('unsupported DOS logical sector length')
    bpb_spt = _int(v['bpb_sectors_per_track'], 'BPB sectors per track', 1, 255)
    bpb_heads = _int(v['bpb_heads'], 'BPB heads', 1, 255)
    if transport == 'fdd' and (bpb_spt, bpb_heads) != (blocks_per_track, heads):
        raise ContractError('FDD BPB geometry must match its physical geometry')
    if transport != 'fdd' and (bpb_spt, bpb_heads) != (32, 8):
        raise ContractError('HDD BPB geometry is advisory 512-byte logical geometry 32x8')
    total = _int(v['total_logical_sectors'], 'BPB total sectors', 1, 0xffffffff)
    _int(v['hidden_sectors'], 'BPB hidden sectors', 0, 0xffffffff)
    _int(v['reserved_sectors'], 'BPB reserved sectors', 1, 1)
    _int(v['fat_count'], 'BPB FAT count', 2, 2)
    if v['fat_bits'] not in (12, 16):
        raise UnsupportedProfileError('only FAT12/FAT16 profiles are selected')
    spc = _int(v['sectors_per_cluster'], 'BPB sectors per cluster', 1, 64)
    if spc & (spc - 1) or spc * bps > 32768:
        raise ContractError('invalid cluster size')
    root_entries = _int(v['root_entries'], 'BPB root entries', 16, 512)
    if root_entries * 32 % bps:
        raise ContractError('root directory must occupy whole sectors')
    _int(v['media_descriptor'], 'BPB media descriptor', 0xf0, 0xff)
    _int(v['volume_serial'], 'BPB volume serial', 0, 0xffffffff)
    _text(v['volume_label'], 'BPB volume label', r'[A-Z0-9-]{1,11}')

    q = p['qualification']
    _object(q, QUALIFICATION_FIELDS, 'qualification')
    if q['m17'] not in {'HOST_VALIDATION_PENDING', 'HOST_VALIDATED'}:
        raise ContractError('invalid M17 qualification label')
    if q['guest'] != 'NOT_QUALIFIED' or q['hardware'] != 'NOT_RUN':
        raise ContractError('M17 fixtures cannot assert guest or hardware qualification')
    if (q['planned_data_milestone'], q['planned_boot_milestone'],
            q['planned_write_milestone']) != (expected_data, expected_boot, expected_write):
        raise ContractError('downstream qualification handoff mismatch')

    layout = fat_layout(p)
    if not 4 <= layout['cluster_count'] <= 65524:
        raise UnsupportedProfileError('selected FAT profile is outside DOS FAT12/FAT16 cluster range')
    return p


def validate_document(document):
    _object(document, ROOT_FIELDS, 'profile document')
    if type(document['schema_version']) is not int or document['schema_version'] != 2:
        raise ContractError('unsupported media profile schema version')
    if document['contract_id'] != 'pc88va-storage-m17-v1':
        raise ContractError('unexpected M17 storage contract id')
    validate_evidence(document['evidence'])
    profiles = document['profiles']
    if not isinstance(profiles, list) or not profiles:
        raise ContractError('profiles must be a nonempty array')
    names = []
    for profile in profiles:
        validate_profile(profile)
        names.append(profile['name'])
        refs = profile['evidence_refs']
        if (not isinstance(refs, list) or not refs or
                any(not isinstance(ref, str) or not ref for ref in refs) or
                len(set(refs)) != len(refs)):
            raise ContractError('profile evidence_refs must be nonempty and unique')
        if any(ref not in document['evidence'] for ref in refs):
            raise ContractError(f"{profile['name']}: unresolved evidence reference")
        if not {'m16-baseline', 'fdkernel-m16'} <= set(refs):
            raise ContractError(f"{profile['name']}: baseline/source evidence is incomplete")
        if profile['device']['transport'] in {'sasi', 'scsi'} and 'vaeg-storage-m16' not in refs:
            raise ContractError(f"{profile['name']}: controller source evidence is incomplete")
        if profile['device']['transport'] == 'scsi' and 'owner-scope' not in refs:
            raise ContractError(f"{profile['name']}: SCSI boot exclusion evidence is missing")
    if len(set(names)) != len(names):
        raise ContractError('duplicate profile name')
    if set(names) != EXPECTED_PROFILES:
        raise ContractError('profile set differs from the M17 acceptance set')
    return profiles


def load(path):
    try:
        document = json.loads(Path(path).read_text(encoding='utf-8'),
                              object_pairs_hook=_unique_json_object)
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(f'cannot read profile document: {error}') from error
    return validate_document(document)


def checked_device_range(lba, count, capacity_blocks):
    """Validate a nonempty device-block interval without wrapping."""
    try:
        _int(lba, 'device LBA', 0, 0xffffffff)
        _int(count, 'device block count', 1, 0xffffffff)
        _int(capacity_blocks, 'device capacity blocks', 1, 0xffffffff)
    except ContractError as error:
        raise RangeError(str(error)) from error
    end = lba + count
    if end > 0x100000000 or end > capacity_blocks:
        raise RangeError('device LBA/count exceeds capacity or 32-bit address space')
    return lba, end


def volume_range_to_device_blocks(start_sector, sector_count, volume_sector_count,
                                  logical_sector_bytes, device_block_bytes,
                                  volume_start_device_blocks, device_capacity_blocks):
    """Map a bounded DOS-sector interval to device blocks without wrap or escape."""
    try:
        _int(start_sector, 'volume LBA', 0, 0xffffffff)
        _int(sector_count, 'requested volume sector count', 1, 0xffffffff)
        _int(volume_sector_count, 'volume capacity sectors', 1, 0xffffffff)
        _int(logical_sector_bytes, 'logical sector bytes', 1, 1024 * 1024)
        _int(device_block_bytes, 'device block bytes', 1, 1024 * 1024)
        _int(volume_start_device_blocks, 'volume start block', 0, 0xffffffff)
        _int(device_capacity_blocks, 'device capacity blocks', 1, 0xffffffff)
    except ContractError as error:
        raise RangeError(str(error)) from error
    if start_sector + sector_count > volume_sector_count:
        raise RangeError('logical-sector range exceeds the selected volume')
    byte_start = start_sector * logical_sector_bytes
    byte_count = sector_count * logical_sector_bytes
    if byte_start % device_block_bytes or byte_count % device_block_bytes:
        raise RangeError('logical-sector range is not device-block aligned')
    block_start = volume_start_device_blocks + byte_start // device_block_bytes
    block_count = byte_count // device_block_bytes
    checked_device_range(block_start, block_count, device_capacity_blocks)
    return block_start, block_count


def assign_block_units(sasi_units=(), scsi_units=(), lastdrive='E'):
    """Model deterministic DOS letters after the two accepted FDD units."""
    if not isinstance(sasi_units, (list, tuple)) or not isinstance(scsi_units, (list, tuple)):
        raise ContractError('unit lists required')
    if not isinstance(lastdrive, str) or not re.fullmatch(r'[C-Z]', lastdrive):
        raise ContractError('LASTDRIVE must be an uppercase drive letter C-Z')
    units = [('fdd', 0), ('fdd', 1)]
    for kind, values, low, high in (('sasi', sasi_units, 0, 1),
                                     ('scsi', scsi_units, 0, 6)):
        if len(set(values)) != len(values):
            raise ContractError(f'duplicate {kind} unit')
        for value in values:
            _int(value, f'{kind} unit', low, high)
            units.append((kind, value))
    max_index = ord(lastdrive) - ord('A')
    if len(units) - 1 > max_index:
        raise ContractError('registered block units exceed LASTDRIVE')
    return [
        {'dos_unit': index, 'drive': chr(ord('A') + index),
         'owner': owner, 'native_unit': unit}
        for index, (owner, unit) in enumerate(units)
    ]
