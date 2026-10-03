#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check settled guest output from msdos4-guest-input.txt; never a build input.

The JSON record is guest evidence. Keep it in persistent Git-excluded storage.
This does not establish unrun machine models, RAM settings or hardware results.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/m19'))
from media import inspect


def check(base, guest):
    for name, data in base.items():
        if guest.get(name) != data:
            raise ValueError('original payload changed: ' + name)
    required = ['CLS.TXT', 'VER.TXT', 'PRE.TXT', 'POST.TXT', 'COPY.TXT', 'TYPE.TXT',
                'ENV.TXT', 'FOR.TXT', 'EXIST.TXT', 'PIPE.TXT', 'CHILD.TXT', 'SWITCH.TXT',
                'ERR.TXT', 'RUNCOM.TXT', 'RUNMZ.TXT', 'ASMCOM.TXT', 'ASMMZ.TXT',
                'CALL.TXT', 'BATCH.TXT', 'LAST.TXT', 'DONE.TXT', 'HZ.ASM', 'HELLO.COM', 'MZDEMO.EXE']
    if any(name not in guest for name in required):
        raise ValueError('incomplete guest command sequence')
    if any(name in guest for name in ('HX.ASM', 'HY.ASM', 'BAD.TXT')):
        raise ValueError('rename/delete/missing-source behavior differs')
    if guest['HZ.ASM'] != base['HELLO.ASM'] or guest['TYPE.TXT'] != base['HELLO.ASM']:
        raise ValueError('copy/type bytes differ')
    for name, lines in [('ENV.TXT', ['OK']), ('FOR.TXT', ['ONE', 'TWO']),
                        ('EXIST.TXT', ['COPYOK']), ('PIPE.TXT', ['PIPEOK']),
                        ('CHILD.TXT', ['CHILDOK']), ('CALL.TXT', ['CALLOK']),
                        ('BATCH.TXT', ['BATCHOK']), ('DONE.TXT', ['FINISHED'])]:
        actual = [s.strip() for s in guest[name].decode('ascii').splitlines() if s.strip()]
        if actual != lines:
            raise ValueError('unexpected output: ' + name)
    switch_lines = [s.strip() for s in guest['SWITCH.TXT'].decode('ascii').splitlines() if s.strip()]
    if switch_lines not in (['SWITCHOK'], ['Invalid switch', 'SWITCHOK']):
        raise ValueError('invalid-switch child did not complete')
    if b'1 File(s) copied' not in guest['COPY.TXT'] or not guest['ERR.TXT'].strip():
        raise ValueError('COPY success/error evidence missing')
    if guest['CLS.TXT'] != b'\x1b[2J\x1b[H':
        raise ValueError('CLS did not preserve redirected output')
    if b'6.22' not in guest['VER.TXT']:
        raise ValueError('native FreeDOS version not retained')
    for name in ('PRE.TXT', 'POST.TXT'):
        if b'MCB chain: VALID' not in guest[name] or b'invalid chain' in guest[name]:
            raise ValueError('MCB validation failed: ' + name)
    for name, message in [('RUNCOM.TXT', b'Hello from PC-88VA FreeDOS!'),
                          ('RUNMZ.TXT', b'MZ relocation and DOS return succeeded.'),
                          ('ASMCOM.TXT', b'0 errors'), ('ASMMZ.TXT', b'0 errors')]:
        if message not in guest[name]:
            raise ValueError('build/COM/MZ execution evidence missing: ' + name)
    if guest['LAST.TXT'] != guest['POST.TXT']:
        raise ValueError('MCB accounting did not stabilize after batch exit')
    if not guest['HELLO.COM']:
        raise ValueError('empty COM')
    mz = guest['MZDEMO.EXE']
    if len(mz) < 28 or mz[:2] != b'MZ' or struct.unpack_from('<H', mz, 6)[0] < 1:
        raise ValueError('missing relocatable MZ')
    return {'scope': 'settled file/readback checks only; screen/CLS checked separately',
            'original_payloads_unchanged': True,
            'file_batch_pipe_child_shell_com_mz_checks': True,
            'mcb_checks_before_after': True,
            'mcb_reports_byte_equal': guest['PRE.TXT'] == guest['POST.TXT']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--guest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output_path = args.output.resolve()
    if output_path.is_relative_to(ROOT) and subprocess.run(
            ['git', 'check-ignore', '-q', str(output_path)], cwd=ROOT).returncode:
        raise ValueError('guest evidence output must be outside Git-tracked source paths')
    spec = json.loads((ROOT / 'config/m19/media.json').read_text())
    original, modified = args.baseline.read_bytes(), args.guest.read_bytes()
    _, base = inspect(original, spec)
    _, guest = inspect(modified, spec)
    record = check(base, guest)
    record.update(baseline_sha256=hashlib.sha256(original).hexdigest(),
                  guest_sha256=hashlib.sha256(modified).hexdigest())
    with args.output.open('x') as output:
        output.write(json.dumps(record, indent=2) + '\n')
    print('Guest readback checks passed; no unrun coverage inferred.')


if __name__ == '__main__':
    main()
