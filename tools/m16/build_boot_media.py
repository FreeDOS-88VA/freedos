#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compose bootable M16 media for the documented PC-88VA FAT12 profiles."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m16'))
from build_loader import build_stage, validate_overlay
from compose_image import compose
from loader_profile import definitions
from media import inspect


class BootMediaError(ValueError):
    pass


def profile_inputs(profile, base_media, base_loader):
    required = {'name', 'capacity_kib', 'd88_disk_type', 'geometry',
                'filesystem', 'format_id'}
    if not isinstance(profile, dict) or set(profile) != required:
        raise BootMediaError('Boot profile fields differ from schema')
    if profile['name'] not in {'2d-320', '2d-360', '2dd-640', '2dd-720',
                               '2hd-1232', '2hd-1280'}:
        raise BootMediaError('Unsupported boot profile')
    geometry = dict(profile['geometry'])
    actual_bytes = (geometry['bytes_per_sector'] * geometry['cylinders'] *
                    geometry['heads'] * geometry['sectors_per_track'])
    if actual_bytes != profile['capacity_kib'] * 1024:
        raise BootMediaError('Capacity does not match profile geometry')
    geometry['encoding'] = 'MFM'
    geometry['track_order'] = 'cylinder_major_head_minor'
    geometry['total_sectors'] = (geometry['cylinders'] * geometry['heads'] *
                                 geometry['sectors_per_track'])
    geometry['total_bytes'] = actual_bytes
    spec = copy.deepcopy(base_media)
    spec['geometry'] = geometry
    fs = copy.deepcopy(profile['filesystem'])
    bps = geometry['bytes_per_sector']
    root_sectors = (fs['root_entries'] * 32 + bps - 1) // bps
    total = actual_bytes // bps
    data_sectors = (total - fs['reserved_sectors'] -
                    fs['fat_count'] * fs['sectors_per_fat'] - root_sectors)
    if data_sectors <= 0 or data_sectors % fs['sectors_per_cluster']:
        raise BootMediaError('Profile does not have an integral FAT12 data area')
    clusters = data_sectors // fs['sectors_per_cluster']
    fat_bytes = (clusters + 2) * 3 // 2 + ((clusters + 2) % 2)
    if fat_bytes > fs['sectors_per_fat'] * bps:
        raise BootMediaError('FAT does not hold the profile data clusters')
    fs.update(fat_type='FAT12', hidden_sectors=0, data_clusters=clusters,
              fat_bytes_required=fat_bytes, first_data_sector=1 +
              fs['fat_count'] * fs['sectors_per_fat'] + root_sectors,
              root_directory_sectors=root_sectors,
              fat_timestamp_policy='source_date_epoch_utc_truncated_to_even_second',
              unallocated_data_policy='zero')
    spec['filesystem'] = fs
    spec['d88']['disk_name'] = 'FDOS-M16-' + profile['name'].upper()
    spec['d88']['disk_type'] = profile['d88_disk_type']
    spec['d88']['sector_size_code'] = 2 if bps == 512 else 3
    spec['d88']['populated_tracks'] = geometry['cylinders'] * geometry['heads']
    spec['d88']['declared_size'] = (spec['d88']['header_size'] +
        geometry['cylinders'] * geometry['heads'] *
        geometry['sectors_per_track'] *
        (spec['d88']['sector_header_size'] + bps))
    spec['boot_record']['bpb_layout'] = 'extended'
    spec['boot_record']['signature_offsets'] = [510] + ([1022] if bps == 1024 else [])
    overlay = copy.deepcopy(base_loader)
    disk = overlay['layout']['disk']
    disk.update(sector_bytes=bps, sectors_track=geometry['sectors_per_track'],
                heads=geometry['heads'], total_sectors=total)
    overlay['bootstrap']['loaded_bytes'] = bps
    # The native PC-88VA FDC firmware takes the sector-size code in DL:
    # 02h for 512-byte sectors and 03h for 1024-byte sectors. The shared
    # adapter template defaults to the M16 1024-byte native boot profile.
    callback, replacements = re.subn(r'(?m)^mov dl, 3$',
                                     f'mov dl, {bps.bit_length() - 8}',
                                     overlay['firmware_callback'])
    if replacements != 1:
        raise BootMediaError('Firmware sector-size selector is not uniquely bound')
    overlay['firmware_callback'] = callback
    # One 2 KiB buffer alignment satisfies both 512 and 1024 byte metadata.
    validate_overlay(overlay)
    definitions(overlay['layout'])
    return spec, overlay


def build(payloads, profile, base_media, base_loader, output, epoch):
    spec, overlay = profile_inputs(profile, base_media, base_loader)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    loader_dir = output / 'loader'
    stage2 = build_stage(overlay, loader_dir, 2)
    complete_payloads = dict(payloads)
    complete_payloads['LOADER.BIN'] = (loader_dir / 'stage2.bin').read_bytes()
    image = compose(complete_payloads, overlay, output, epoch, spec)
    _, files = inspect(image, spec)
    if files != complete_payloads:
        raise BootMediaError('Filesystem readback differs from boot payloads')
    manifest = {'profile': profile, 'sha256': hashlib.sha256(image).hexdigest(),
                'size': len(image), 'files_verified': sorted(files),
                'loader_stage2': stage2}
    (output / 'boot-media.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return image, spec, overlay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--payload-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((ROOT / 'config/m16/boot-profiles.json').read_text())
    profile = next((p for p in config['profiles'] if p['name'] == args.profile), None)
    if profile is None:
        parser.error('Unknown M16 boot profile')
    media = json.loads((ROOT / 'config/m16/media.json').read_text())
    loader = json.loads((ROOT / 'config/m16/loader.json').read_text())
    accepted = {'KERNEL.SYS', 'COMMAND.COM', 'COUNTRY.SYS', 'SYSVA.EXE',
                'COMPROBE.COM', 'DOSINPUT.COM', 'DOSREPT.COM', 'MZPROBE.EXE',
                'SYS.ID', 'TYPEA.TXT', 'TYPEB.TXT', 'COMDATA.TXT'}
    payloads = {p.name.upper(): p.read_bytes() for p in args.payload_dir.iterdir()
                if p.is_file() and p.name.upper() in accepted}
    outputs = {name for name in payloads if name != 'LOADER.BIN'}
    if 'KERNEL.SYS' not in outputs or 'COMMAND.COM' not in outputs:
        parser.error('Kernel and command shell payloads are required')
    image, _, _ = build(payloads, profile, media, loader, args.output, 1787814827)
    target = args.output / 'media.d88'
    target.write_bytes(image)
    print(f'Built {profile["name"]} boot media: {target}')


if __name__ == '__main__':
    main()
