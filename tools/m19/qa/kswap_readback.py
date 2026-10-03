#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed settled VA KSSF QA readback, with component regression provenance.

Probe/accounting algorithm maintained locally from the independent FreeCOM
regression at f5512b5a1756768830b541a274ac48973c46de12. No PC acceptance state
is inherited. Guest-written artifacts are evidence only, never build inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/m19'))
from media import inspect


def probe(data):
    match = re.fullmatch(rb'PSP allocation paragraphs: ([0-9A-F]{4})\r\n'
                         rb'Live COMMAND-named MCBs: ([0-9A-F]{4})\r\n', data)
    if not match:
        raise ValueError('missing or malformed MCB probe result')
    return tuple(int(value, 16) for value in match.groups())


def check_screen(text):
    for message in (b'PANIC', b'context is missing', b'String #', b'MCB chain corrupt'):
        if message in text:
            raise ValueError('guest error diagnostic despite completed files')
    lines = text.rstrip().splitlines()
    if not lines or lines[-1].strip() != b'A:\\>':
        raise ValueError('guest did not return to the root prompt')


def check(base, guest):
    for name, data in base.items():
        if guest.get(name) != data:
            raise ValueError('original payload changed: ' + name)
    baseline = probe(guest.get('BASE.OUT', b''))
    first = probe(guest.get('FIRST.OUT', b''))
    samples = [probe(guest.get('S%02d.OUT' % i, b'')) for i in range(20)]
    if baseline[1] <= 0:
        raise ValueError('ordinary child did not retain COMMAND')
    if any(owners != 0 or allocation <= baseline[0] for allocation, owners in [first, *samples]):
        raise ValueError('swap did not release COMMAND or gain memory')
    if len(set([first, *samples])) != 1:
        raise ValueError('repeated swaps changed allocation accounting')
    for name, expected in [('ARGS.OUT', b'ARGUMENTS'), ('ENV.TXT', b'HELLO'),
                           ('ENV2.TXT', b'HELLO'), ('ALIAS.TXT', b'ALIASOK'),
                           ('ALIAS2.TXT', b'ALIASOK'), ('RC.TXT', b'7'),
                           ('DONE.TXT', b'FINISHED')]:
        if guest.get(name, b'').strip() != expected:
            raise ValueError('lost state or incomplete execution: ' + name)
    if b'set KEEP=HELLO' not in guest.get('HIST.TXT', b''):
        raise ValueError('lost history')
    if guest.get('MZ.OK') != b'MZ relocation OK\r\n':
        raise ValueError('swapped MZ did not execute')
    for name in ('PRE.TXT', 'POST.TXT', 'LAST.TXT'):
        data = guest.get(name, b'')
        if b'MCB chain: VALID' not in data or b'invalid chain' in data:
            raise ValueError('MCB validation absent or failed: ' + name)
    if guest['POST.TXT'] != guest['LAST.TXT']:
        raise ValueError('MCB accounting did not settle')
    for name, expected in [('ASMCOM.TXT', b'0 errors'), ('ASMMZ.TXT', b'0 errors'),
                           ('RUNCOM.TXT', b'Hello from PC-88VA FreeDOS!'),
                           ('RUNMZ.TXT', b'MZ relocation and DOS return succeeded.')]:
        if expected not in guest.get(name, b''):
            raise ValueError('source assembly or normal EXEC missing: ' + name)
    if not guest.get('HELLO.COM'):
        raise ValueError('missing assembled COM')
    mz = guest.get('MZDEMO.EXE', b'')
    if len(mz) < 28 or mz[:2] != b'MZ' or struct.unpack_from('<H', mz, 6)[0] < 1:
        raise ValueError('missing assembled relocatable MZ')
    return {'scope': 'settled VA KSSF state/COM/MZ/MCB readback only',
            'ordinary_probe': baseline, 'swapped_probe': first, 'repeated_swaps': 20,
            'original_payloads_unchanged': True, 'checks_passed': True,
            'hardware': 'NOT RUN', 'startup_requires_separate_visual_check': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--guest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--screen-text', type=Path, required=True,
                        help='separately inspected final console text; not a build input')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT) and subprocess.run(
            ['git', 'check-ignore', '-q', str(output)], cwd=ROOT).returncode:
        raise ValueError('guest evidence must not be placed in tracked source paths')
    spec = json.loads((ROOT / 'config/m19/media.json').read_text())
    original, modified = args.baseline.read_bytes(), args.guest.read_bytes()
    _, base = inspect(original, spec)
    _, guest = inspect(modified, spec)
    screen = args.screen_text.read_bytes()
    check_screen(screen)
    record = check(base, guest)
    record.update(screen_text_sha256=hashlib.sha256(screen).hexdigest(),
                  screen_diagnostics_checked=True)
    record.update(baseline_sha256=hashlib.sha256(original).hexdigest(),
                  guest_sha256=hashlib.sha256(modified).hexdigest())
    with args.output.open('x') as stream:
        stream.write(json.dumps(record, indent=2) + '\n')
    print('KSSF settled readback passed; unrun configurations/hardware not inferred.')


if __name__ == '__main__':
    main()
