# SPDX-License-Identifier: GPL-2.0-or-later
"""Strict public fixture profile contract; not a claim of guest support."""
import json
import re
from pathlib import Path

FIELDS = {'name', 'container', 'physical_sector_bytes', 'cylinders', 'heads',
          'sectors_per_track', 'logical_sector_bytes', 'fat_bits',
          'sectors_per_cluster', 'root_entries', 'media_descriptor',
          'partition_start', 'volume_serial', 'volume_label'}


def validate(p):
    if not isinstance(p, dict) or set(p) != FIELDS:
        raise ValueError('unknown or missing profile fields')
    for key in FIELDS - {'name', 'container', 'volume_label'}:
        if type(p[key]) is not int:
            raise ValueError('integer required: ' + key)
    if not isinstance(p['name'], str) or not re.fullmatch(r'[a-z0-9-]{1,40}', p['name']):
        raise ValueError('invalid profile name')
    if not isinstance(p['volume_label'], str) or not re.fullmatch(r'[A-Z0-9-]{1,11}', p['volume_label']):
        raise ValueError('invalid label')
    if p['container'] not in ('raw', 'hdi', 'vhd'):
        raise ValueError('unsupported container')
    physical, logical = p['physical_sector_bytes'], p['logical_sector_bytes']
    if physical not in (256, 512, 1024) or logical not in (512, 1024) or logical % physical:
        raise ValueError('unsupported sector conversion')
    c, h, s = p['cylinders'], p['heads'], p['sectors_per_track']
    if not (1 <= c <= 65535 and 1 <= h <= 255 and 1 <= s <= 255):
        raise ValueError('invalid geometry')
    size = c * h * s * physical
    if size > 64 * 1024 * 1024 or size % logical:
        raise ValueError('fixture capacity outside bounded profile')
    if p['container'] == 'hdi' and (physical, c, h, s) != (256, 615, 8, 33):
        raise ValueError('only the selected public SASI geometry is supported')
    if p['container'] == 'vhd' and (h != 8 or s != 32 or size % (1024 * 1024)):
        raise ValueError('VHD fixture geometry mismatch')
    if p['container'] != 'raw' and logical != 512:
        raise ValueError('HDD DOS-sector policy is 512 bytes')
    spc = p['sectors_per_cluster']
    if spc not in (1, 2, 4, 8, 16, 32, 64) or spc * logical > 32768:
        raise ValueError('unsupported cluster size')
    if p['fat_bits'] not in (12, 16) or not 16 <= p['root_entries'] <= 512:
        raise ValueError('invalid FAT/root profile')
    if p['root_entries'] * 32 % logical:
        raise ValueError('root directory must occupy whole sectors')
    if not 0xf0 <= p['media_descriptor'] <= 0xff or not 0 <= p['volume_serial'] <= 0xffffffff:
        raise ValueError('invalid media or serial')
    start = p['partition_start']
    if start not in (0, 2048) or (start and (p['container'] != 'vhd' or p['fat_bits'] != 16)):
        raise ValueError('only unpartitioned or selected MBR data profiles are supported')
    if size // logical - start < 100:
        raise ValueError('partition outside disk')
    return p


def load(path):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or set(data) != {'schema_version', 'profiles'} or type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('invalid profile document')
    if not isinstance(data['profiles'], list) or not data['profiles']:
        raise ValueError('profiles must be nonempty')
    profiles = [validate(p) for p in data['profiles']]
    if len({p['name'] for p in profiles}) != len(profiles):
        raise ValueError('duplicate profile')
    return profiles
