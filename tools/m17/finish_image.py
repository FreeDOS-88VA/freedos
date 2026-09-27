#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Connect the compiled DOS components, carrier, loader and fresh filesystem."""
import argparse
import hashlib
import json
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
                 'COMPROBE.COM', 'CFGSTATE.COM', 'DOSINPUT.COM', 'DOSREPT.COM', 'MZPROBE.EXE')}
    payloads['CONFIG.SYS'] = (ROOT / 'config/m17/CONFIG.SYS').read_text().replace('\n', '\r\n').encode('ascii')
    payloads['SYS.ID'] = b'M16SOURCE\r\n'
    payloads['TYPEA.TXT'] = b'M13-TYPE-A!\r\n'
    payloads['TYPEB.TXT'] = b'M13-TYPE-B!\r\n'
    payloads['COMDATA.TXT'] = b'M13-COM-DATA\r\n'
    compose(payloads, profile, out, 1787814827)
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


if __name__ == '__main__':
    main()
