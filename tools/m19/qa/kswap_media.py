#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Clean-build all M19 inputs twice, then compose separate repaired KSSF QA disks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/m19'))
from compose_image import compose
from media import inspect


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    subprocess.run([sys.executable, '-B', str(ROOT / 'tools/m19/build_image.py'),
                    '--output', str(out / 'normal'), '--dist', str(out / 'normal-dist')], check=True)
    subprocess.run([sys.executable, '-B', str(ROOT / 'tools/m19/verify_distribution.py'),
                    '--dist', str(out / 'normal-dist')], check=True)
    profile = json.loads((ROOT / 'config/m19/loader.json').read_text())
    geometry = json.loads((ROOT / 'config/m19/media.json').read_text())
    epoch = json.loads((ROOT / 'config/m19/host-tooling.json').read_text())['source_date_epoch']
    records = []
    for size in (512, 8192):
        images = []
        for number in (1, 2):
            run = out / 'normal' / ('run-' + str(number))
            _, payloads = inspect((run / 'media.d88').read_bytes(), geometry)
            payloads = dict(payloads)
            config = (ROOT / 'config/m19/CONFIG.SYS').read_text()
            if 'SHELL=' in config:
                raise ValueError('normal configuration already overrides the shell')
            config += 'SHELL=A:\\KSSF.COM A:\\COMMAND.COM /E:%d /P\n' % size
            payloads['CONFIG.SYS'] = config.replace('\n', '\r\n').encode('ascii')
            payloads['AUTOEXEC.BAT'] = (
                b'@ECHO OFF\r\nSET PATH=A:\\' + b'\r\n'
                b'PROMPT $P$G\r\nECHO KSSF VA QA READY\r\n')
            for name in ('PROBE.COM', 'SWAPMZ.EXE'):
                payloads[name] = (run / name).read_bytes()
            payloads['KSWAPQA.TXT'] = b'Experimental paired KSSF/COMMAND only. Not a normal release.\r\n'
            work = out / ('media-%d-%d' % (size, number))
            work.mkdir()
            data = compose(payloads, profile, work, epoch)
            _, observed = inspect(data, geometry)
            if observed != payloads:
                raise ValueError('KSSF QA media readback differs')
            if (work / 'stage1/stage1.bin').read_bytes() != (run / 'stage1/stage1.bin').read_bytes():
                raise ValueError('KSSF QA changed loader bytes')
            images.append(data)
        if images[0] != images[1]:
            raise ValueError('independent full KSSF QA builds differ')
        name = 'KSWAP-E%d.D88' % size
        (out / name).write_bytes(images[0])
        records.append({'filename': name, 'environment_bytes': size,
                        'sha256': digest(images[0]), 'size_bytes': len(images[0])})
    record = {'scope': 'isolated experimental VA KSSF pair, not a released distribution',
              'parent_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'component_lock_sha256': digest((ROOT / 'manifests/m19-components.lock.json').read_bytes()),
              'two_complete_builds_equal': True, 'disks': records,
              'guest': 'NOT RUN BY BUILD', 'hardware': 'NOT RUN'}
    (out / 'qa-build.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Two full KSSF QA builds agree; guest/hardware qualification is separate.')


if __name__ == '__main__':
    main()
