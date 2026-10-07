#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the PC-88VA MS-DOS 2.0 experiment disk.

The VA boot sector, IO.SYS BIOS part and MEMINFO come from the pinned
experiment branch of the MS-DOS component.  IO.SYS links that BIOS with
the Microsoft-supplied 2.0 SYSINIT.OBJ and SYSIMES.OBJ; MSDOS.SYS and
COMMAND.COM are the Microsoft-supplied 2.0 binaries of the same MIT
release (the published 2.0 source tree is incomplete).  MASM 5.10 and
LINK 3.65 from the v4.0 tree run under emu2 built from its pinned source.

This experiment is self-contained: it uses no milestone tools.
"""
import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

BIOSSEG = 0x1000
SECTOR = 1024
TOTAL = 1280
SPT, HEADS = 8, 2
RESERVED, FATS, FAT_SECTORS, ROOT_ENTRIES = 1, 2, 2, 192
MEDIA = 0xFE
ROOT_SECTORS = ROOT_ENTRIES * 32 // SECTOR
FIRST_DATA = RESERVED + FATS * FAT_SECTORS + ROOT_SECTORS
# Offsets of the VABOOT fields filled here.
BOOT_EXTENT = 62
SIGNATURES = (510, 1022)
# SOURCE_DATE_EPOCH for directory timestamps: 1983-03-01 00:00:00 UTC.
FAT_DATE = ((1983 - 1980) << 9) | (3 << 5) | 1
FAT_TIME = 0


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(component, commit, paths, dest):
    """Extract paths of a component commit with git archive."""
    data = subprocess.run(['git', '-C', str(component), 'archive', '--format=tar', commit, *paths],
                          check=True, stdout=subprocess.PIPE).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(dest, filter='data')
    return digest(data)


def mz_image(exe, base=None, origin=0):
    """Return the load image of an MZ file, applying relocations at base."""
    if exe[:2] != b'MZ':
        raise ValueError('not an MZ executable')
    last, pages, nrel, header, _, _, ss, sp, _, ip, cs, relofs = struct.unpack_from('<12H', exe, 2)
    size = pages * 512 - (512 - last if last else 0) - header * 16
    image = bytearray(exe[header * 16:header * 16 + size])
    if nrel and base is None:
        raise ValueError('relocations present but no load segment given')
    for n in range(nrel):
        offset, segment = struct.unpack_from('<HH', exe, relofs + 4 * n)
        where = segment * 16 + offset
        value = struct.unpack_from('<H', image, where)[0]
        struct.pack_into('<H', image, where, (value + base) & 0xFFFF)
    if cs != 0 or ip != origin:
        raise ValueError('unexpected entry point %04X:%04X' % (cs, ip))
    return bytes(image[origin:])


def fat12_set(fat, cluster, value):
    i = cluster * 3 // 2
    if cluster & 1:
        fat[i] = (fat[i] & 0x0F) | ((value << 4) & 0xF0)
        fat[i + 1] = (value >> 4) & 0xFF
    else:
        fat[i] = value & 0xFF
        fat[i + 1] = (fat[i + 1] & 0xF0) | ((value >> 8) & 0x0F)


def compose(boot, files):
    """Return a raw FAT12 image; files is an ordered list of (name, data, attr)."""
    raw = bytearray(TOTAL * SECTOR)
    fat = bytearray(FAT_SECTORS * SECTOR)
    fat12_set(fat, 0, 0xF00 | MEDIA)
    fat12_set(fat, 1, 0xFFF)
    root = bytearray(ROOT_SECTORS * SECTOR)
    cluster, extents = 2, {}
    for index, (name, data, attr) in enumerate(files):
        count = (len(data) + SECTOR - 1) // SECTOR
        first = cluster if count else 0
        for n in range(count):
            fat12_set(fat, cluster + n, cluster + n + 1 if n + 1 < count else 0xFFF)
            lba = FIRST_DATA + cluster + n - 2
            raw[lba * SECTOR:(lba + 1) * SECTOR] = data[n * SECTOR:(n + 1) * SECTOR].ljust(SECTOR, b'\0')
        extents[name] = (FIRST_DATA + cluster - 2, count)
        cluster += count
        stem, _, ext = name.partition('.')
        entry = struct.pack('<8s3sB10sHHHI', stem.ljust(8).encode(), ext.ljust(3).encode(), attr,
                            bytes(10), FAT_TIME, FAT_DATE, first, len(data))
        root[index * 32:(index + 1) * 32] = entry
    if cluster - 2 > TOTAL - FIRST_DATA:
        raise ValueError('files exceed the disk')
    sector = bytearray(boot.ljust(SECTOR, b'\0'))
    struct.pack_into('<8sHBHBHHBHHHI', sector, 3, b'MSDOS2VA', SECTOR, 1, RESERVED, FATS,
                     ROOT_ENTRIES, TOTAL, MEDIA, FAT_SECTORS, SPT, HEADS, 0)
    io_lba, io_count = extents['IO.SYS']
    dos_lba, dos_count = extents['MSDOS.SYS']
    if dos_lba != io_lba + io_count:
        raise ValueError('IO.SYS and MSDOS.SYS must be contiguous')
    struct.pack_into('<HHH', sector, BOOT_EXTENT, io_lba, io_count + dos_count, io_count)
    for offset in SIGNATURES:
        sector[offset:offset + 2] = b'\x55\xaa'
    raw[:SECTOR] = sector
    for n in range(FATS):
        offset = (RESERVED + n * FAT_SECTORS) * SECTOR
        raw[offset:offset + len(fat)] = fat
    offset = (RESERVED + FATS * FAT_SECTORS) * SECTOR
    raw[offset:offset + len(root)] = root
    return bytes(raw), extents


def d88(raw, name):
    """Wrap a raw 2HD image as D88 (cylinder-major, head-minor, sector IDs 1-8)."""
    header = bytearray(0x2B0)
    header[:len(name)] = name.encode('ascii')
    header[0x1B] = 0x20
    track_bytes = SPT * (16 + SECTOR)
    tracks = TOTAL // SPT
    struct.pack_into('<I', header, 0x1C, len(header) + tracks * track_bytes)
    out = bytearray()
    for track in range(tracks):
        struct.pack_into('<I', header, 0x20 + 4 * track, len(header) + track * track_bytes)
        cylinder, head = divmod(track, HEADS)
        for r in range(SPT):
            out += struct.pack('<BBBBHBBB5sH', cylinder, head, r + 1, 3, SPT, 0, 0, 0, bytes(5), SECTOR)
            lba = track * SPT + r
            out += raw[lba * SECTOR:(lba + 1) * SECTOR]
    return bytes(header + out)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads((HERE / 'lock.json').read_text())
    out = args.output.resolve()
    if out.exists():
        raise SystemExit('output directory exists: %s' % out)
    work = out / 'work'
    work.mkdir(parents=True)

    msdos = lock['msdos']
    archive_digest = export(ROOT / 'components/msdos', msdos['commit'], msdos['paths'], out / 'msdos')
    emu2_src = out / 'emu2'
    export(ROOT / 'components/emu2', lock['emu2']['commit'], ['.'], emu2_src)
    with (out / 'emu2-build.log').open('wb') as log:
        subprocess.run(['make', '-j2'], cwd=emu2_src, stdout=log, stderr=subprocess.STDOUT, check=True)
    emu = emu2_src / 'emu2'

    inputs = {}
    for name, relative in lock['microsoft_inputs'].items():
        data = (out / 'msdos' / relative).read_bytes()
        if digest(data) != lock['microsoft_sha256'][name]:
            raise SystemExit('input digest mismatch: ' + name)
        inputs[name] = data
    for name in ('MASM.EXE', 'LINK.EXE', 'SYSINIT.OBJ', 'SYSIMES.OBJ'):
        (work / name).write_bytes(inputs[name])
    # MASM 5.10 reads DOS text: give it CRLF line ends.
    for source in sorted((out / 'msdos/v2.0/pc88va').glob('*.ASM')):
        text = source.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        (work / source.name).write_bytes(text)

    env = {k: v for k, v in os.environ.items() if not k.startswith('EMU2_')}
    env.update(EMU2_DRIVE_C=str(work), EMU2_DEFAULT_DRIVE='C:', EMU2_CWD='C:\\', EMU2_DOSVER='4.00')
    step = [0]

    def dos(tool, *arguments):
        step[0] += 1
        log = out / '{:02d}-{}.log'.format(step[0], tool.split('.')[0])
        with log.open('wb') as handle:
            subprocess.run([str(emu), str(work / tool), *arguments], cwd=work, env=env,
                           stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           check=True, timeout=120)
        text = log.read_bytes().decode('latin-1')
        if any(int(n) for n in re.findall(r'(\d+) Severe', text)) or re.search(r'error [AL]\d', text):
            raise SystemExit('tool reported errors, see ' + str(log))

    for module in ('VAIO', 'VABOOT', 'MEMINFO'):
        dos('MASM.EXE', module + ';')
    dos('LINK.EXE', 'VAIO+SYSINIT+SYSIMES,IO.EXE,IO.MAP;')
    dos('LINK.EXE', 'VABOOT,VABOOT.EXE;')
    dos('LINK.EXE', 'MEMINFO,MEMINFO.EXE;')

    iosys = mz_image((work / 'io.exe').read_bytes(), base=BIOSSEG)
    boot = mz_image((work / 'vaboot.exe').read_bytes())
    if len(boot) > min(SIGNATURES):
        raise SystemExit('boot sector code overlaps the signature')
    meminfo = mz_image((work / 'meminfo.exe').read_bytes(), origin=0x100)
    autoexec = b'MEMINFO > MEMINFO.TXT\r\nMEMINFO\r\n'
    files = [('IO.SYS', iosys, 0x07), ('MSDOS.SYS', inputs['MSDOS.SYS'], 0x07),
             ('COMMAND.COM', inputs['COMMAND.COM'], 0x20), ('AUTOEXEC.BAT', autoexec, 0x20),
             ('MEMINFO.COM', meminfo, 0x20)]
    raw, extents = compose(boot, files)
    image = d88(raw, 'MSDOS2-PC88VA')
    (out / 'msdos2-va.d88').write_bytes(image)
    record = {
        'experiment': 'msdos2-va',
        'msdos_commit': msdos['commit'],
        'msdos_archive_sha256': archive_digest,
        'emu2_commit': lock['emu2']['commit'],
        'emu2_sha256': digest(emu.read_bytes()),
        'microsoft_sha256': lock['microsoft_sha256'],
        'files': {name: {'sha256': digest(data), 'size': len(data), 'first_lba': extents[name][0],
                         'sectors': extents[name][1]} for name, data, _ in files},
        'boot_sha256': digest(boot),
        'd88_sha256': digest(image),
    }
    (out / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'d88': str(out / 'msdos2-va.d88'), 'sha256': record['d88_sha256']}))


if __name__ == '__main__':
    main()
