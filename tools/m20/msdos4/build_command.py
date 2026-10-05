#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build MS-DOS 4.0 COMMAND.COM for the M20 system disk.

Maintained M20 copy of the MS-DOS 4 COMMAND recipe (build_msdos4.py) of M19
Preview 1, parent f5f73ae09ff2037aed75de71bd5be3c503462409. The original
Microsoft BUILDIDX, BUILDMSG, MASM 5.10, LINK 3.65 and EXE2BIN from the pinned
MIT source tree run under the pinned emu2, which is built here from source.
No saved message file or DOS output is an input.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

MODULES = ('COMMAND1 COMMAND2 RUCODE RDATA INIT IPARSE UINIT TCODE TBATCH TBATCH2 '
           'TFOR TCMD1A TCMD1B TCMD2A TCMD2B TENV TENV2 TMISC1 TMISC2 TPIPE '
           'PARSE2 PATH1 PATH2 TUCODE COPY COPYPR1 COPYPR2 CPARSE TPARSE TPRINTF '
           'TDATA TSPC').split()
TOOLS = ('BUILDIDX', 'BUILDMSG', 'MASM', 'LINK', 'EXE2BIN')
# FREEDOS accepts the FreeDOS kernel version and F8 /Y; PC88VA selects the VA
# console behaviour of the fork.
DEFINITIONS = ['/DFREEDOS', '/DPC88VA']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def link_response(modules):
    if not modules or len(set(modules)) != len(modules):
        raise ValueError('missing or duplicate link modules')
    if any(not name.isascii() or not name.isalnum() for name in modules):
        raise ValueError('invalid module name')
    text = '+\r\n'.join(m + '.OBJ' for m in modules) + ',COMMAND.EXE,COMMAND.MAP,;\r\n'
    if any(len(line) > 127 for line in text.splitlines()):
        raise ValueError('LINK 3.65 response line exceeds DOS buffer')
    return text.encode('ascii')


def build(msdos, emu2_source, out, revisions):
    """Build COMMAND.COM from component trees; return its build record."""
    out.mkdir(parents=True)
    emu2 = out / 'emu2'
    shutil.copytree(emu2_source, emu2)
    with (out / 'emu2-build.log').open('wb') as log:
        subprocess.run(['make', '-j2'], cwd=emu2, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    emu = emu2 / 'emu2'
    source = msdos / 'v4.0/src'
    work = out / 'work'
    work.mkdir()
    # Preserve original bytes and source names; the DOS runner resolves case.
    for directory in ['INC', 'CMD/COMMAND']:
        for path in sorted((source / directory).iterdir()):
            if path.suffix.upper() in ('.ASM', '.INC', '.SKL', '.SW', '.EQU'):
                (work / path.name.upper()).write_bytes(path.read_bytes())
    (work / 'USA-MS.MSG').write_bytes((source / 'MESSAGES/USA-MS.MSG').read_bytes())
    identities = {}
    for name in TOOLS:
        data = (source / ('TOOLS/' + name + '.EXE')).read_bytes()
        (work / (name + '.EXE')).write_bytes(data)
        identities[name] = {'sha256': digest(data), 'size_bytes': len(data)}
    env = {k: v for k, v in os.environ.items() if not k.startswith('EMU2_')}
    env.update(EMU2_DRIVE_C=str(work), EMU2_DEFAULT_DRIVE='C:',
               EMU2_CWD='C:\\', EMU2_DOSVER='4.00')
    step = [0]

    def dos(tool, *arguments):
        step[0] += 1
        with (out / '{:02d}-{}.log'.format(step[0], tool)).open('wb') as log:
            subprocess.run([str(emu), str(work / (tool + '.EXE')), *arguments],
                           cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, check=True, timeout=120)

    dos('BUILDIDX', 'USA-MS.MSG')
    dos('BUILDMSG', 'USA-MS', 'COMMAND.SKL')
    for module in MODULES:
        dos('MASM', *DEFINITIONS, module + '.ASM;')
        if not (work / (module.lower() + '.obj')).is_file():
            raise ValueError('assembler output missing: ' + module)
    (work / 'CMD.LNK').write_bytes(link_response(MODULES))
    dos('LINK', '@CMD.LNK')
    dos('EXE2BIN', 'COMMAND.EXE', 'COMMAND.COM')
    binary = (work / 'command.com').read_bytes()
    if not 20000 < len(binary) < 65280:
        raise ValueError('MS-DOS 4 COMMAND.COM size is implausible')
    (out / 'COMMAND.COM').write_bytes(binary)
    record = {'source_revisions': revisions, 'assembler_definitions': DEFINITIONS,
              'original_tools': identities, 'modules': MODULES,
              'file_sha256': digest(binary), 'file_size_bytes': len(binary),
              'host_tool': 'emu2 built from the pinned component with the container C compiler',
              'emu2_sha256': digest(emu.read_bytes())}
    (out / 'msdos4-build.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Built MS-DOS 4 COMMAND.COM: {} bytes'.format(len(binary)))
    return record
