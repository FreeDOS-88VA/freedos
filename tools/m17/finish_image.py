#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Connect the compiled DOS components, carrier, loader and fresh filesystem."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
from compose_image import compose, ROOT

sys.path.insert(0, str(ROOT / 'tools/m17'))
from build_compressed_kernel import build
from build_loader import build_stage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    profile = json.loads((ROOT / 'config/m17/loader.json').read_text())
    carrier = build(out / 'kernel-linked.exe',
                    ROOT / 'components/fdkernel/pc88va/kernel/m13_unpack.asm',
                    out / 'KERNEL.SYS', load_segment=0x2700, file_segment=0x2700,
                    scratch_segment=0x3700, source_offset=4096,
                    ring_offset=0, ring_segment=0x3800,
                    compact_bridge=True, link_map=out / 'kernel.map')
    limit = max(carrier['minimum_runtime_memory_top'],
                *(hi for lo, hi in profile['layout']['regions'].values()))
    if limit > 256 * 1024:
        raise ValueError('Boot layout no longer fits the 256 KiB capacity contract')
    (out / 'carrier.json').write_text(json.dumps(carrier, indent=2)+'\n')
    loader = out / 'loader'
    loader.mkdir()
    build_stage(profile, loader, 2)
    (out / 'LOADER.BIN').write_bytes((loader / 'stage2.bin').read_bytes())
    payloads = {name: (out / name).read_bytes() for name in
                ('KERNEL.SYS', 'LOADER.BIN', 'COMMAND.COM', 'COUNTRY.SYS', 'SYSVA.EXE',
                 'COMPROBE.COM', 'CFGSTATE.COM', 'CFGMEM.COM', 'CFGPROBE.COM',
                 'CFGDEV.SYS', 'CFGNONE.SYS', 'DOSINPUT.COM', 'DOSREPT.COM',
                 'MZPROBE.EXE')}
    payloads['CONFIG.SYS'] = (ROOT / 'config/m17/CONFIG.SYS').read_text().replace('\n', '\r\n').encode('ascii')
    payloads['SYS.ID'] = b'M16SOURCE\r\n'
    payloads['TYPEA.TXT'] = b'M13-TYPE-A!\r\n'
    payloads['TYPEB.TXT'] = b'M13-TYPE-B!\r\n'
    payloads['COMDATA.TXT'] = b'M13-COM-DATA\r\n'
    compose(payloads, profile, out, 1787814827)
    build_config_qa(payloads, profile, out)
    from build_floppy_media import build_profiles
    build_profiles(ROOT / 'config/m17/floppy-profiles.json', out / 'floppy-media', 1787814827)
    import subprocess
    storage = out / 'storage-media'
    subprocess.run([sys.executable, str(ROOT / 'tools/m17/produce.py'), '--profiles', str(ROOT / 'config/m17/media-profiles.json'), '--output', str(storage)], check=True)
    subprocess.run([sys.executable, str(ROOT / 'tools/m17/inspect_storage.py'), '--profiles', str(ROOT / 'config/m17/media-profiles.json'), '--directory', str(storage)], check=True)
    artifacts = {p.relative_to(out).as_posix(): {
                     'size': p.stat().st_size,
                     'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in out.rglob('*') if p.is_file() and p.name != 'artifacts.json'}
    (out / 'artifacts.json').write_text(json.dumps(artifacts, indent=2)+'\n')


def build_config_qa(payloads, loader_profile, output):
    """Build separate, disposable startup images for real CONFIG/DEVICE tests."""
    import hashlib
    source = ROOT / 'config/m17/config-qa.json'
    document = json.loads(source.read_text(encoding='utf-8'))
    if (set(document) != {'schema_version', 'profiles'} or
            type(document['schema_version']) is not int or
            document['schema_version'] != 1 or not isinstance(document['profiles'], list)):
        raise ValueError('Invalid M17 CONFIG QA profile document')
    expected = {'baseline-config', 'fdconfig-precedence', 'character-init',
                'zero-unit-init', 'loadseg-2000'}
    rows = document['profiles']
    if (any(not isinstance(row, dict) for row in rows) or
            {row.get('name') for row in rows} != expected or
            len(rows) != len(expected)):
        raise ValueError('M17 CONFIG QA profile set mismatch')
    qa_root = output / 'config-qa'
    qa_root.mkdir()
    records = []
    for row in rows:
        required = {'name', 'config_source', 'fdconfig_source', 'loadseg',
                    'device_driver', 'expected_config_file'}
        if set(row) != required:
            raise ValueError('M17 CONFIG QA profile has unknown or missing fields')
        if row['config_source'] not in {'CONFIG.SYS', 'CONFIG.loadseg-2000.SYS'}:
            raise ValueError('CONFIG QA source is outside config/m17')
        if row['fdconfig_source'] not in {None, 'FDCONFIG.control',
                                          'FDCONFIG.character',
                                          'FDCONFIG.zero-units'}:
            raise ValueError('FDCONFIG QA source is outside config/m17')
        if row['loadseg'] not in {'1000', '2000'}:
            raise ValueError('CONFIG QA LOADSEG outside selected policy')
        config_path = ROOT / 'config/m17' / row['config_source']
        config_text = config_path.read_text(encoding='ascii')
        match = re.search(r'^PC88VA_LOADSEG=([0-9A-Fa-f]+)h?\s*$', config_text,
                          flags=re.MULTILINE)
        if not match or match.group(1).upper() != row['loadseg']:
            raise ValueError('CONFIG QA LOADSEG does not match its profile')
        qa_payloads = dict(payloads)
        qa_payloads['CONFIG.SYS'] = config_text.replace('\n', '\r\n').encode('ascii')
        fdconfig_sha256 = None
        if row['fdconfig_source'] is not None:
            fdconfig_path = ROOT / 'config/m17' / row['fdconfig_source']
            fdconfig = fdconfig_path.read_text(encoding='ascii')
            fdconfig_sha256 = hashlib.sha256(fdconfig.replace('\n', '\r\n').encode('ascii')).hexdigest()
            qa_payloads['FDCONFIG.SYS'] = fdconfig.replace('\n', '\r\n').encode('ascii')
        if row['expected_config_file'] not in {'CONFIG.SYS', 'FDCONFIG.SYS'}:
            raise ValueError('Invalid expected CONFIG filename')
        if (row['fdconfig_source'] is None) != (row['expected_config_file'] == 'CONFIG.SYS'):
            raise ValueError('CONFIG/FDCONFIG precedence expectation is inconsistent')
        directory = qa_root / row['name']
        directory.mkdir()
        from compose_image import compose
        image = compose(qa_payloads, loader_profile, directory, 1787814827)
        records.append({
            'name': row['name'],
            'image': row['name'] + '/media.d88',
            'size_bytes': len(image),
            'sha256': hashlib.sha256(image).hexdigest(),
            'config_source': row['config_source'],
            'config_sha256': hashlib.sha256(qa_payloads['CONFIG.SYS']).hexdigest(),
            'fdconfig_source': row['fdconfig_source'],
            'fdconfig_sha256': fdconfig_sha256,
            'loader_loadseg': row['loadseg'],
            'device_driver': row['device_driver'],
            'expected_config_file': row['expected_config_file'],
        })
    manifest = {'schema_version': 1,
                'profile_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'profiles': records}
    (qa_root / 'manifest.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
