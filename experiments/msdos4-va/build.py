#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the PC-88VA MS-DOS 4.0 distribution disk.

Every program is built from the MIT-licensed MS-DOS 4.0 sources on the
pinned release/msdos-va branch of the MS-DOS component, with the original
tools (NMAKE, BUILDIDX, BUILDMSG, NOSRVBLD, MASM 5.10, CL, LINK 3.65,
EXE2BIN) running under emu2 built from its pinned source.  NMAKE builds
MSDOS.SYS, the SYSINIT objects, the utilities and COUNTRY.SYS from their
original makefiles; the PC-88VA BIOS part of IO.SYS, the boot sector and
FORMAT/SYS come from pc88va/ and v4.0/pc88va/.

This experiment is self-contained: it uses no milestone tools.
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

# Text files get CRLF line ends: NOSRVBLD and MASM read DOS text.
TEXT = ('.ASM', '.INC', '.SKL', '.MSG', '.LNK', '.CTL', '.C', '.H', '.INI', '.BAT',
        '.EQU', '.SW', '.DEF', '.MAK', '.TXT', '.LST', '.DAT', '.CL1')
DEFINES = ('extasw=-DPC88VA', 'extcsw=-DPC88VA')
SYSINIT_OBJECTS = ('SYSINIT1', 'SYSCONF', 'SYSINIT2', 'SYSIMES')
COMMAND_MODULES = ('COMMAND1 COMMAND2 RUCODE RDATA INIT IPARSE UINIT TCODE TBATCH '
                   'TBATCH2 TFOR TCMD1A TCMD1B TCMD2A TCMD2B TENV TENV2 TMISC1 TMISC2 '
                   'TPIPE PARSE2 PATH1 PATH2 TUCODE COPY COPYPR1 COPYPR2 CPARSE TPARSE '
                   'TPRINTF TDATA TSPC').split()
ERRORS = re.compile(r'error [ACLU]\d{4}|fatal error|^Stop\.|Extended Error|'
                    r'[1-9]\d* Severe +Errors|Unresolved externals|Out of memory', re.M | re.I)


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


def crlf_tree(top):
    for path in sorted(top.rglob('*')):
        name = path.name.upper()
        if path.is_file() and (name.endswith(TEXT) or name == 'MAKEFILE'):
            path.write_bytes(dos_text(path.read_bytes()))


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
    """Return a raw FAT12 image: boot sector, label, files in order."""
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
    """MASM source defining BOOTCODE, the 1024-byte boot sector."""
    lines = ['BOOTCODE LABEL BYTE']
    lines += ['        DB      ' + ','.join('%03XH' % b for b in boot[i:i + 16])
              for i in range(0, len(boot), 16)]
    return ('\r\n'.join(lines) + '\r\n').encode('ascii')


class Dos:
    """Run DOS tools under emu2 and fail on any reported error."""

    def __init__(self, emu, logs, drive_root):
        self.emu, self.logs, self.root, self.step = emu, logs, drive_root, 0

    def run(self, cwd, program, *arguments, env=()):
        self.step += 1
        log = self.logs / '{:03d}-{}-{}.log'.format(
            self.step, cwd.name.lower(), Path(program).stem.lower())
        dos_cwd = ('D:\\' + str(cwd.relative_to(self.root)).replace('/', '\\')).upper()
        host = {k: v for k, v in os.environ.items() if not k.startswith('EMU2_')}
        host.update(EMU2_DRIVE_D=str(self.root), EMU2_DEFAULT_DRIVE='D:', EMU2_CWD=dos_cwd,
                    EMU2_DOSVER='4.00')
        command = [str(self.emu), str(program), *arguments]
        if env:
            command += ['--', *env]
        with log.open('wb') as handle:
            subprocess.run(command, cwd=cwd, env=host, stdout=handle, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, check=True, timeout=3600)
        text = log.read_bytes().decode('latin-1')
        if ERRORS.search(text):
            raise SystemExit('tool reported errors, see ' + str(log))
        return text


def expect(path):
    for candidate in path.parent.iterdir():
        if candidate.name.lower() == path.name.lower():
            return candidate.read_bytes()
    raise SystemExit('missing build output: ' + str(path))


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
    root = tree / 'v4.0'
    src = root / 'src'
    tools = src / 'TOOLS'
    for name, expected in lock['tool_sha256'].items():
        if digest((tools / name).read_bytes()) != expected:
            raise SystemExit('tool digest mismatch: ' + name)
    crlf_tree(tree)
    dos = Dos(emu2_src / 'emu2', logs, root)

    # Bootstrap COMMAND.COM: NMAKE needs a command interpreter for COPY and
    # DEL.  Assemble it module by module as in the 4.0 makefile.
    boot_cmd = out / 'bootstrap-command'
    shutil.copytree(src / 'CMD/COMMAND', boot_cmd)
    for path in (src / 'INC').iterdir():
        if path.is_file() and not (boot_cmd / path.name).exists():
            shutil.copy(path, boot_cmd / path.name)
    for tool in ('BUILDIDX.EXE', 'BUILDMSG.EXE', 'MASM.EXE', 'LINK.EXE', 'EXE2BIN.EXE'):
        shutil.copy(tools / tool, boot_cmd)
    shutil.copy(src / 'MESSAGES/USA-MS.MSG', boot_cmd)
    dos.root = out
    dos.run(boot_cmd, boot_cmd / 'BUILDIDX.EXE', 'USA-MS.MSG')
    dos.run(boot_cmd, boot_cmd / 'BUILDMSG.EXE', 'USA-MS', 'COMMAND.SKL')
    for module in COMMAND_MODULES:
        dos.run(boot_cmd, boot_cmd / 'MASM.EXE', '-Mx', '-t', '-DPC88VA', module + '.ASM;')
    (boot_cmd / 'CMD.LNK').write_bytes(('+\r\n'.join(m + '.OBJ' for m in COMMAND_MODULES)
                                        + ',COMMAND.EXE,,;\r\n').encode('ascii'))
    dos.run(boot_cmd, boot_cmd / 'LINK.EXE', '@CMD.LNK')
    dos.run(boot_cmd, boot_cmd / 'EXE2BIN.EXE', 'COMMAND.EXE', 'COMMAND.COM')
    bootstrap_command = expect(boot_cmd / 'COMMAND.COM')
    (tools / 'COMMAND.COM').write_bytes(bootstrap_command)
    dos.root = root

    env = ('PATH=D:\\SRC\\TOOLS', 'COMSPEC=D:\\SRC\\TOOLS\\COMMAND.COM', 'INIT=D:\\SRC\\TOOLS',
           'INCLUDE=D:\\SRC\\TOOLS\\BLD\\INC', 'LIB=D:\\SRC\\TOOLS\\BLD\\LIB', 'COUNTRY=usa-ms')

    def nmake(directory, *targets):
        return dos.run(src / directory, tools / 'NMAKE.EXE', *DEFINES, *targets, env=env)

    # Top-level makefile order.  The DOS makefile builds INC through
    # "cd ..\\inc", which does not carry across emu2 processes, so make the
    # message include it needs, then INC, then the rest of DOS.
    nmake('MESSAGES')
    nmake('MAPPER')
    nmake('DOS', 'msdos.cl1')
    nmake('INC')
    nmake('DOS')
    nmake('BIOS', 'msbio.cl1', *(m.lower() + '.obj' for m in SYSINIT_OBJECTS))
    built = {}
    for name, (directory, product) in lock['programs'].items():
        nmake(directory)
        built[name] = expect(src / directory / product)
    nmake('CMD/COMMAND')
    msdos_sys = expect(src / 'DOS/msdos.sys')
    command = expect(src / 'CMD/COMMAND/command.com')
    if command != bootstrap_command:
        raise SystemExit('NMAKE COMMAND.COM differs from the bootstrap build')

    # PC-88VA parts.
    va = out / 'va'
    va.mkdir()
    for path in sorted((tree / 'pc88va').iterdir()) + sorted((root / 'pc88va').iterdir()):
        shutil.copy(path, va / path.name.upper())
    for module in SYSINIT_OBJECTS:
        shutil.copy(src / 'BIOS' / (module.lower() + '.obj'), va / (module + '.OBJ'))
    for tool in ('MASM.EXE', 'LINK.EXE'):
        shutil.copy(tools / tool, va)
    dos.root = out
    dos.run(va, va / 'MASM.EXE', 'VABOOT;')
    dos.run(va, va / 'LINK.EXE', 'VABOOT,VABOOT.EXE;')
    boot = mz_image(expect(va / 'VABOOT.EXE'))
    (va / 'VABOOT.INC').write_bytes(boot_include(boot))
    for module in ('VAIO', 'VAFORMAT', 'VASYS'):
        dos.run(va, va / 'MASM.EXE', module + ';')
    (va / 'IO.LNK').write_bytes(('VAIO+' + '+'.join(SYSINIT_OBJECTS) + ',IO.EXE,IO.MAP;\r\n')
                                .encode('ascii'))
    dos.run(va, va / 'LINK.EXE', '@IO.LNK')
    dos.run(va, va / 'LINK.EXE', 'VAFORMAT,VAFORMAT.EXE;')
    dos.run(va, va / 'LINK.EXE', 'VASYS,VASYS.EXE;')
    iosys = mz_image(expect(va / 'IO.EXE'), base=BIOSSEG)
    built['FORMAT.COM'] = mz_image(expect(va / 'VAFORMAT.EXE'), origin=0x100)
    built['SYS.COM'] = mz_image(expect(va / 'VASYS.EXE'), origin=0x100)

    disk = lock['disk']
    fat_date = ((disk['date'][0] - 1980) << 9) | (disk['date'][1] << 5) | disk['date'][2]
    text = {name: dos_text((HERE / 'disk' / name).read_bytes()) for name in disk['text_files']}
    text['LICENSE.TXT'] = dos_text((tree / 'LICENSE').read_bytes())
    files = [('IO.SYS', iosys, 0x07), ('MSDOS.SYS', msdos_sys, 0x07),
             ('COMMAND.COM', command, 0x20)]
    files += [(name, text[name], 0x20) for name in sorted(text)]
    files += [(name, built[name], 0x20) for name in sorted(built)]
    serial = int(disk['serial'].replace('-', ''), 16)
    raw = compose(boot, files, disk['label'], fat_date, serial)
    image = d88(raw, disk['d88_name'])
    (out / disk['image']).write_bytes(image)
    record = {
        'distribution': 'msdos4-va',
        'msdos_commit': msdos['commit'],
        'msdos_archive_sha256': archive_digest,
        'emu2_commit': lock['emu2']['commit'],
        'tool_sha256': lock['tool_sha256'],
        'boot_sha256': digest(boot),
        'files': {name: {'sha256': digest(data), 'size': len(data)} for name, data, _ in files},
        'image': {'name': disk['image'], 'sha256': digest(image), 'size': len(image)},
    }
    (out / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record['image']))


if __name__ == '__main__':
    main()
