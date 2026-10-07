#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the PC-88VA MS-DOS 4.0 experiment disk.

MSDOS.SYS, the SYSINIT part of IO.SYS and COMMAND.COM are assembled from
the MIT-licensed MS-DOS 4.0 sources on the pinned experiment branch of the
MS-DOS component; the PC-88VA BIOS part replaces the IBM PC BIOS part of
IO.SYS.  The boot sector and MEMINFO are shared with the MS-DOS 2.0
experiment sources on the same branch.  The original BUILDIDX, BUILDMSG,
NOSRVBLD, MASM 5.10 and LINK 3.65 run under emu2 built from its pinned
source.

This experiment is self-contained: it uses no milestone tools.  The D88
writer, FAT12 composer and MZ loader are maintained copies of those in
experiments/msdos2-va/build.py.
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
BOOT_EXTENT = 62
SIGNATURES = (510, 1022)
# Directory timestamps: 1988-06-17 00:00:00.
FAT_DATE = ((1988 - 1980) << 9) | (6 << 5) | 17
FAT_TIME = 0

TOOLS = ('BUILDIDX', 'BUILDMSG', 'NOSRVBLD', 'MASM', 'LINK', 'EXE2BIN')
TEXT = ('.ASM', '.INC', '.SKL', '.MSG', '.LNK', '.CTL')
SYSINIT_MODULES = ('SYSINIT1', 'SYSCONF', 'SYSINIT2', 'SYSIMES')
DOS_INC_MODULES = ('NIBDOS', 'CONST2', 'MSDATA', 'MSTABLE', 'MSDOSME')
COMMAND_MODULES = ('COMMAND1 COMMAND2 RUCODE RDATA INIT IPARSE UINIT TCODE TBATCH '
                   'TBATCH2 TFOR TCMD1A TCMD1B TCMD2A TCMD2B TENV TENV2 TMISC1 TMISC2 '
                   'TPIPE PARSE2 PATH1 PATH2 TUCODE COPY COPYPR1 COPYPR2 CPARSE TPARSE '
                   'TPRINTF TDATA TSPC').split()
# PC88VA selects the native text BIOS for CLS in COMMAND and skips the IBM
# BIOS probes in SYSINIT1; FREEDOS is not defined.
DEFINES = ('-DPC88VA',)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(component, commit, paths, dest):
    data = subprocess.run(['git', '-C', str(component), 'archive', '--format=tar', commit, *paths],
                          check=True, stdout=subprocess.PIPE).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(dest, filter='data')
    return digest(data)


def dos_text(data):
    """CRLF line ends, as the DOS tools expect."""
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


def compose(boot, files):
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
    struct.pack_into('<8sHBHBHHBHHHI', sector, 3, b'MSDOS4VA', SECTOR, 1, RESERVED, FATS,
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


class Dos:
    """Run original DOS build tools under emu2 in per-directory work trees."""

    def __init__(self, emu, logs):
        self.emu, self.logs, self.step = emu, logs, 0

    def run(self, work, tool, *arguments):
        self.step += 1
        log = self.logs / '{:03d}-{}-{}.log'.format(self.step, work.name, tool.split('.')[0])
        env = {k: v for k, v in os.environ.items() if not k.startswith('EMU2_')}
        env.update(EMU2_DRIVE_C=str(work), EMU2_DEFAULT_DRIVE='C:', EMU2_CWD='C:\\',
                   EMU2_DOSVER='4.00')
        with log.open('wb') as handle:
            subprocess.run([str(self.emu), str(work / tool), *arguments], cwd=work, env=env,
                           stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           check=True, timeout=300)
        text = log.read_bytes().decode('latin-1')
        if (any(int(n) for n in re.findall(r'(\d+) Severe', text)) or
                re.search(r'error [AL]\d|^Error', text, re.M)):
            raise SystemExit('tool reported errors, see ' + str(log))
        return text

    def masm(self, work, module, defines=()):
        self.run(work, 'MASM.EXE', '-Mx', '-t', *defines, module + '.ASM;')
        if not (work / (module.lower() + '.obj')).is_file():
            raise SystemExit('assembler output missing: ' + module)


def layer(work, source, directories, tools, message):
    """Overlay source directories in order; later ones win, as with -I. first."""
    work.mkdir(parents=True)
    for directory in directories:
        for path in sorted((source / directory).iterdir()):
            if path.is_file():
                data = path.read_bytes()
                name = path.name.upper()
                (work / name).write_bytes(dos_text(data) if name.endswith(TEXT) else data)
    for tool, data in tools.items():
        (work / (tool + '.EXE')).write_bytes(data)
    (work / 'USA-MS.MSG').write_bytes(dos_text(message))


def link_response(modules, output, extra=''):
    text = '+\r\n'.join(m + '.OBJ' for m in modules) + '\r\n' + output + '\r\n' + extra + ';\r\n'
    if any(len(line) > 127 for line in text.splitlines()):
        raise ValueError('LINK response line exceeds DOS buffer')
    return text.encode('ascii')


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
    archive_digest = export(ROOT / 'components/msdos', msdos['commit'], msdos['paths'], out / 'msdos')
    emu2_src = out / 'emu2'
    export(ROOT / 'components/emu2', lock['emu2']['commit'], ['.'], emu2_src)
    with (logs / 'emu2-build.log').open('wb') as log:
        subprocess.run(['make', '-j2'], cwd=emu2_src, stdout=log, stderr=subprocess.STDOUT, check=True)
    dos = Dos(emu2_src / 'emu2', logs)

    source = out / 'msdos/v4.0/src'
    tools = {}
    for tool in TOOLS:
        data = (source / 'TOOLS' / (tool + '.EXE')).read_bytes()
        if digest(data) != lock['tool_sha256'][tool]:
            raise SystemExit('tool digest mismatch: ' + tool)
        tools[tool] = data
    message = (source / 'MESSAGES/USA-MS.MSG').read_bytes()
    work = out / 'work'
    inc, dosdir, bios, cmd, va = (work / n for n in ('inc', 'dos', 'bios', 'cmd', 'va'))
    layer(inc, source, ('DOS', 'INC'), tools, message)
    layer(dosdir, source, ('INC', 'DOS'), tools, message)
    layer(bios, source, ('DOS', 'INC', 'BIOS'), tools, message)
    layer(cmd, source, ('INC', 'CMD/COMMAND'), tools, message)
    layer(va, out / 'msdos/v4.0', ('pc88va',), tools, message)
    for name in ('VABOOT.ASM', 'MEMINFO.ASM'):
        (va / name).write_bytes(dos_text((out / 'msdos/v2.0/pc88va' / name).read_bytes()))

    # MSDOS.SYS
    for directory in (inc, dosdir, bios, cmd):
        dos.run(directory, 'BUILDIDX.EXE', 'USA-MS.MSG')
    dos.run(dosdir, 'NOSRVBLD.EXE', 'MSDOS.SKL', 'USA-MS.MSG')
    for path in dosdir.glob('msdos.cl*'):
        shutil.copy(path, inc)
    for module in DOS_INC_MODULES:
        dos.masm(inc, module)
    lnk = (source / 'DOS/MSDOS.LNK').read_text().splitlines()
    dos_modules = [Path(line.strip().rstrip('+').strip().replace('\\', '/')).stem.upper()
                   for line in lnk if line.strip().rstrip('+').strip().lower().endswith('.obj')]
    for module in dos_modules:
        if module in DOS_INC_MODULES:
            shutil.copy(inc / (module.lower() + '.obj'), dosdir)
        else:
            dos.masm(dosdir, module)
    (dosdir / 'MSDOS.LNK').write_bytes(link_response(dos_modules, 'MSDOS.EXE'))
    dos.run(dosdir, 'LINK.EXE', '@MSDOS.LNK')
    dos.run(dosdir, 'EXE2BIN.EXE', 'MSDOS.EXE', 'MSDOS.SYS')
    msdos_sys = (dosdir / 'msdos.sys').read_bytes()

    # IO.SYS: VA BIOS part + SYSINIT
    dos.run(bios, 'NOSRVBLD.EXE', 'MSBIO.SKL', 'USA-MS.MSG')
    for module in SYSINIT_MODULES:
        dos.masm(bios, module, DEFINES)
        shutil.copy(bios / (module.lower() + '.obj'), va)
    for module in ('VAIO', 'VABOOT', 'MEMINFO'):
        dos.masm(va, module)
    (va / 'IO.LNK').write_bytes(link_response(('VAIO',) + SYSINIT_MODULES, 'IO.EXE'))
    dos.run(va, 'LINK.EXE', '@IO.LNK')
    dos.run(va, 'LINK.EXE', 'VABOOT,VABOOT.EXE;')
    dos.run(va, 'LINK.EXE', 'MEMINFO,MEMINFO.EXE;')
    iosys = mz_image((va / 'io.exe').read_bytes(), base=BIOSSEG)
    boot = mz_image((va / 'vaboot.exe').read_bytes())
    if len(boot) > min(SIGNATURES):
        raise SystemExit('boot sector code overlaps the signature')
    meminfo = mz_image((va / 'meminfo.exe').read_bytes(), origin=0x100)

    # COMMAND.COM
    dos.run(cmd, 'BUILDMSG.EXE', 'USA-MS', 'COMMAND.SKL')
    for module in COMMAND_MODULES:
        dos.masm(cmd, module, DEFINES)
    (cmd / 'CMD.LNK').write_bytes(link_response(COMMAND_MODULES, 'COMMAND.EXE'))
    dos.run(cmd, 'LINK.EXE', '@CMD.LNK')
    dos.run(cmd, 'EXE2BIN.EXE', 'COMMAND.EXE', 'COMMAND.COM')
    command = (cmd / 'command.com').read_bytes()

    autoexec = b'MEMINFO > MEMINFO.TXT\r\nMEMINFO\r\n'
    files = [('IO.SYS', iosys, 0x07), ('MSDOS.SYS', msdos_sys, 0x07),
             ('COMMAND.COM', command, 0x20), ('AUTOEXEC.BAT', autoexec, 0x20),
             ('MEMINFO.COM', meminfo, 0x20)]
    images = {}
    for variant, config in lock['configurations'].items():
        extra = [('CONFIG.SYS', config.encode('ascii'), 0x20)] if config else []
        raw, extents = compose(boot, files + extra)
        image = d88(raw, 'MSDOS4-PC88VA')
        name = 'msdos4-va-%s.d88' % variant
        (out / name).write_bytes(image)
        images[name] = digest(image)
    record = {
        'experiment': 'msdos4-va',
        'msdos_commit': msdos['commit'],
        'msdos_archive_sha256': archive_digest,
        'emu2_commit': lock['emu2']['commit'],
        'tool_sha256': lock['tool_sha256'],
        'files': {name: {'sha256': digest(data), 'size': len(data), 'first_lba': extents[name][0],
                         'sectors': extents[name][1]} for name, data, _ in files},
        'boot_sha256': digest(boot),
        'images': images,
    }
    (out / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(images))


if __name__ == '__main__':
    main()
