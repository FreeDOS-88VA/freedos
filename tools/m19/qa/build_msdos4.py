#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Rebuild public MS-DOS 4 COMMAND.COM for isolated compatibility research.

Not a normal M19 distribution producer. Component files are exported from
pinned external Git repositories; no saved message files or DOS outputs are
inputs. Original Microsoft tools are publicly included in the MIT source tree.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

MSDOS = '2d04cacc5322951f187bb17e017c12920ac8ebe2'
EMU2 = '9d8698d06e67359bc8b230c2d19d5b1503e60819'
MODULES = ('COMMAND1 COMMAND2 RUCODE RDATA INIT IPARSE UINIT TCODE TBATCH TBATCH2 '
           'TFOR TCMD1A TCMD1B TCMD2A TCMD2B TENV TENV2 TMISC1 TMISC2 TPIPE '
           'PARSE2 PATH1 PATH2 TUCODE COPY COPYPR1 COPYPR2 CPARSE TPARSE TPRINTF '
           'TDATA TSPC').split()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(repo, revision, out):
    archive = subprocess.check_output(['git', '-C', str(repo), 'archive', revision])
    out.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(out, filter='data')
    return digest(archive)


def assembler_definitions(profile):
    return {'original': [], 'freedos': ['/DFREEDOS'],
            'pc88va': ['/DFREEDOS', '/DPC88VA']}[profile].copy()


def link_response(modules):
    if not modules or len(set(modules)) != len(modules):
        raise ValueError('missing or duplicate link modules')
    if any(not name.isascii() or not name.isalnum() for name in modules):
        raise ValueError('invalid module name')
    text = '+\r\n'.join(m + '.OBJ' for m in modules) + ',COMMAND.EXE,COMMAND.MAP,;\r\n'
    if any(len(line) > 127 for line in text.splitlines()):
        raise ValueError('LINK 3.65 response line exceeds DOS buffer')
    return text.encode('ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--msdos-repo', type=Path, required=True)
    parser.add_argument('--emu2-repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--msdos-revision', default=MSDOS)
    parser.add_argument('--profile', choices=('original', 'freedos', 'pc88va'), default='original')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    if len(args.msdos_revision) != 40 or any(c not in '0123456789abcdef' for c in args.msdos_revision):
        raise ValueError('MS-DOS revision must be a full commit identity')
    pins = {'msdos': args.msdos_revision, 'emu2': EMU2}
    definitions = assembler_definitions(args.profile)
    archives = {}
    for name, repo in [('msdos', args.msdos_repo), ('emu2', args.emu2_repo)]:
        archives[name] = export(repo, pins[name], out / name)
    with (out / 'emu2-build.log').open('wb') as log:
        subprocess.run(['make', '-j2'], cwd=out / 'emu2', stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    source = out / 'msdos/v4.0/src'
    work = out / 'work'
    work.mkdir()
    # Preserve original bytes and source names; the DOS runner resolves case.
    for directory in ['INC', 'CMD/COMMAND']:
        for path in (source / directory).iterdir():
            if path.suffix.upper() in ('.ASM', '.INC', '.SKL', '.SW', '.EQU'):
                (work / path.name.upper()).write_bytes(path.read_bytes())
    (work / 'USA-MS.MSG').write_bytes((source / 'MESSAGES/USA-MS.MSG').read_bytes())
    tools = ['BUILDIDX', 'BUILDMSG', 'MASM', 'LINK', 'EXE2BIN']
    identities = {}
    for name in tools:
        data = (source / ('TOOLS/' + name + '.EXE')).read_bytes()
        (work / (name + '.EXE')).write_bytes(data)
        identities[name] = {'sha256': digest(data), 'size_bytes': len(data)}
    env = {k: v for k, v in os.environ.items() if not k.startswith('EMU2_')}
    env.update(EMU2_DRIVE_C=str(work), EMU2_DEFAULT_DRIVE='C:',
               EMU2_CWD='C:\\', EMU2_DOSVER='4.00')
    emu = out / 'emu2/emu2'

    def dos(tool, *arguments):
        with (out / (tool + '-' + str(len(list(out.glob('*.log')))) + '.log')).open('wb') as log:
            subprocess.run([str(emu), str(work / (tool + '.EXE')), *arguments],
                           cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, check=True, timeout=120)

    dos('BUILDIDX', 'USA-MS.MSG')
    dos('BUILDMSG', 'USA-MS', 'COMMAND.SKL')
    for module in MODULES:
        dos('MASM', *definitions, module + '.ASM;')
        if not (work / (module.lower() + '.obj')).is_file():
            raise ValueError('assembler output missing: ' + module)
    (work / 'CMD.LNK').write_bytes(link_response(MODULES))
    dos('LINK', '@CMD.LNK')
    dos('EXE2BIN', 'COMMAND.EXE', 'COMMAND.COM')
    binary = (work / 'command.com').read_bytes()
    (out / 'COMMAND.COM').write_bytes(binary)
    record = {'scope': 'public MS-DOS 4 shell research; not VA qualification',
              'revisions': pins, 'source_archive_sha256': archives,
              'profile': args.profile, 'assembler_definitions': definitions,
              'original_tools': identities, 'command_sha256': digest(binary),
              'command_size_bytes': len(binary),
              'host_compiler': subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
              'emu2_sha256': digest(emu.read_bytes()), 'guest_execution': 'NOT RUN'}
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
