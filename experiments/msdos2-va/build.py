#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the PC-88VA MS-DOS 2.0 distribution disk.

The PC-88VA BIOS part of IO.SYS, the boot sector and FORMAT/SYS are
assembled from the pinned release/msdos-va branch of the MS-DOS component.
IO.SYS links the BIOS part with the Microsoft-supplied 2.0 SYSINIT.OBJ and
SYSIMES.OBJ; MSDOS.SYS, COMMAND.COM and the utilities are the
Microsoft-supplied 2.0 binaries of the same MIT release, because the
published 2.0 source tree cannot rebuild them.  MASM 5.10 and LINK 3.65
from the v4.0 tree run under emu2 built from its pinned source.

This experiment is self-contained: it uses no milestone tools.  The FAT12
composer, D88 writer and MZ loader are maintained copies of those in
experiments/msdos4-va/build.py.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
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
SIGNATURES = (510, 1022)
ERRORS = re.compile(r'error [AL]\d{4}|fatal error|[1-9]\d* Severe +Errors|Unresolved externals',
                    re.M | re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(component, commit, paths, dest):
    data = subprocess.run(['git', '-C', str(component), 'archive', '--format=tar', commit, *paths],
                          check=True, stdout=subprocess.PIPE).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(dest, filter='data')
    return digest(data)


def dos_text(data):
    return data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')


def mz_image(exe, base=None, origin=0):
    if exe[:2] != b'MZ':
        raise ValueError('not an MZ executable')
    last, pages, nrel, header, _, _, _, _, _, ip, cs, relofs = struct.unpack_from('<12H', exe, 2)
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


def dos_name(name):
    stem, _, ext = name.partition('.')
    if not (1 <= len(stem) <= 8 and len(ext) <= 3) or name != name.upper():
        raise ValueError('bad DOS name: ' + name)
    return stem.ljust(8).encode('ascii') + ext.ljust(3).encode('ascii')


def compose(boot, files, label, fat_date, serial):
    raw = bytearray(TOTAL * SECTOR)
    fat = bytearray(FAT_SECTORS * SECTOR)
    fat12_set(fat, 0, 0xF00 | MEDIA)
    fat12_set(fat, 1, 0xFFF)
    root = bytearray(ROOT_SECTORS * SECTOR)
    entries = [struct.pack('<11sB10sHHHI', label.ljust(11).encode('ascii'), 0x08, bytes(10),
                           0, fat_date, 0, 0)]
    cluster = 2
    for name, data, attr in files:
        count = (len(data) + SECTOR - 1) // SECTOR
        first = cluster if count else 0
        for n in range(count):
            fat12_set(fat, cluster + n, cluster + n + 1 if n + 1 < count else 0xFFF)
            lba = FIRST_DATA + cluster + n - 2
            raw[lba * SECTOR:(lba + 1) * SECTOR] = data[n * SECTOR:(n + 1) * SECTOR].ljust(SECTOR, b'\0')
        cluster += count
        entries.append(struct.pack('<11sB10sHHHI', dos_name(name), attr, bytes(10), 0, fat_date,
                                   first, len(data)))
    if cluster - 2 > TOTAL - FIRST_DATA or len(entries) > ROOT_ENTRIES:
        raise ValueError('files exceed the disk')
    root[:32 * len(entries)] = b''.join(entries)
    sector = bytearray(boot)
    if len(sector) != SECTOR or any(sector[o:o + 2] != b'\x55\xaa' for o in SIGNATURES):
        raise ValueError('boot sector shape')
    struct.pack_into('<I', sector, 39, serial)
    sector[43:54] = label.ljust(11).encode('ascii')
    raw[:SECTOR] = sector
    for n in range(FATS):
        offset = (RESERVED + n * FAT_SECTORS) * SECTOR
        raw[offset:offset + len(fat)] = fat
    offset = (RESERVED + FATS * FAT_SECTORS) * SECTOR
    raw[offset:offset + len(root)] = root
    return bytes(raw)


def d88(raw, name):
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


def boot_include(boot):
    lines = ['BOOTCODE LABEL BYTE']
    lines += ['        DB      ' + ','.join('%03XH' % b for b in boot[i:i + 16])
              for i in range(0, len(boot), 16)]
    return ('\r\n'.join(lines) + '\r\n').encode('ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads((HERE / 'lock.json').read_text())
    out = args.output.resolve()
    if out.exists():
        raise SystemExit('output directory exists: %s' % out)
    out.mkdir(parents=True)
    logs = out / 'logs'
    logs.mkdir()

    msdos = lock['msdos']
    tree = out / 'tree'
    archive_digest = export(ROOT / 'components/msdos', msdos['commit'], msdos['paths'], tree)
    emu2_src = out / 'emu2'
    export(ROOT / 'components/emu2', lock['emu2']['commit'], ['.'], emu2_src)
    with (logs / 'emu2-build.log').open('wb') as log:
        subprocess.run(['make', '-j2'], cwd=emu2_src, stdout=log, stderr=subprocess.STDOUT, check=True)
    emu = emu2_src / 'emu2'

    inputs = {}
    for name, relative in lock['microsoft_inputs'].items():
        data = (tree / relative).read_bytes()
        if digest(data) != lock['microsoft_sha256'][name]:
            raise SystemExit('input digest mismatch: ' + name)
        inputs[name] = data

    work = out / 'work'
    work.mkdir()
    for name in ('MASM.EXE', 'LINK.EXE', 'SYSINIT.OBJ', 'SYSIMES.OBJ'):
        (work / name).write_bytes(inputs[name])
    for directory in ('pc88va', 'v2.0/pc88va'):
        for path in sorted((tree / directory).iterdir()):
            (work / path.name.upper()).write_bytes(dos_text(path.read_bytes()))

    env = {k: v for k, v in os.environ.items() if not k.startswith('EMU2_')}
    env.update(EMU2_DRIVE_C=str(work), EMU2_DEFAULT_DRIVE='C:', EMU2_CWD='C:\\', EMU2_DOSVER='4.00')
    step = [0]

    def dos(tool, *arguments):
        step[0] += 1
        log = logs / '{:02d}-{}.log'.format(step[0], tool.split('.')[0].lower())
        with log.open('wb') as handle:
            subprocess.run([str(emu), str(work / tool), *arguments], cwd=work, env=env,
                           stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           check=True, timeout=300)
        if ERRORS.search(log.read_bytes().decode('latin-1')):
            raise SystemExit('tool reported errors, see ' + str(log))

    def output(name):
        for path in work.iterdir():
            if path.name.lower() == name.lower():
                return path.read_bytes()
        raise SystemExit('missing build output: ' + name)

    dos('MASM.EXE', 'VABOOT;')
    dos('LINK.EXE', 'VABOOT,VABOOT.EXE;')
    boot = mz_image(output('VABOOT.EXE'))
    (work / 'VABOOT.INC').write_bytes(boot_include(boot))
    for module in ('VAIO', 'VAFORMAT', 'VASYS', 'MEMINFO'):
        dos('MASM.EXE', module + ';')
    dos('LINK.EXE', 'VAIO+SYSINIT+SYSIMES,IO.EXE,IO.MAP;')
    dos('LINK.EXE', 'VAFORMAT,VAFORMAT.EXE;')
    dos('LINK.EXE', 'VASYS,VASYS.EXE;')
    dos('LINK.EXE', 'MEMINFO,MEMINFO.EXE;')
    iosys = mz_image(output('IO.EXE'), base=BIOSSEG)

    programs = {name: inputs[name] for name in lock['release_programs']}
    programs['FORMAT.COM'] = mz_image(output('VAFORMAT.EXE'), origin=0x100)
    programs['SYS.COM'] = mz_image(output('VASYS.EXE'), origin=0x100)
    programs['MEMINFO.COM'] = mz_image(output('MEMINFO.EXE'), origin=0x100)

    disk = lock['disk']
    fat_date = ((disk['date'][0] - 1980) << 9) | (disk['date'][1] << 5) | disk['date'][2]
    text = {name: dos_text((HERE / 'disk' / name).read_bytes()) for name in disk['text_files']}
    text['LICENSE.TXT'] = dos_text((tree / 'LICENSE').read_bytes())
    files = [('IO.SYS', iosys, 0x07), ('MSDOS.SYS', inputs['MSDOS.SYS'], 0x07),
             ('COMMAND.COM', inputs['COMMAND.COM'], 0x20)]
    files += [(name, text[name], 0x20) for name in sorted(text)]
    files += [(name, programs[name], 0x20) for name in sorted(programs)]
    serial = int(disk['serial'].replace('-', ''), 16)
    image = d88(compose(boot, files, disk['label'], fat_date, serial), disk['d88_name'])
    (out / disk['image']).write_bytes(image)
    record = {
        'distribution': 'msdos2-va',
        'msdos_commit': msdos['commit'],
        'msdos_archive_sha256': archive_digest,
        'emu2_commit': lock['emu2']['commit'],
        'emu2_sha256': digest(emu.read_bytes()),
        'microsoft_sha256': lock['microsoft_sha256'],
        'boot_sha256': digest(boot),
        'files': {name: {'sha256': digest(data), 'size': len(data)} for name, data, _ in files},
        'image': {'name': disk['image'], 'sha256': digest(image), 'size': len(image)},
    }
    (out / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record['image']))


if __name__ == '__main__':
    main()
