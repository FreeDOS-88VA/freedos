#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Complete normal M19 rebuild plus two fresh MS-DOS 4 shell QA builds.

No old D88 or saved executable is an input. This does NOT replace the normal
FreeCOM distribution. SYS transfer of this experimental shell is not qualified.
"""
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
    parser.add_argument('--msdos-repo', type=Path, required=True)
    parser.add_argument('--emu2-repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    spec = json.loads((ROOT / 'config/m19/msdos4-research.json').read_text())
    for name, repo in [('msdos', args.msdos_repo), ('emu2', args.emu2_repo)]:
        archive = subprocess.check_output(['git', '-C', str(repo), 'archive', spec[name]['commit']])
        if digest(archive) != spec[name]['source_archive_sha256']:
            raise ValueError('research source archive differs: ' + name)
    subprocess.run([sys.executable, '-B', str(ROOT / 'tools/m19/build_image.py'),
                    '--output', str(out / 'normal'), '--dist', str(out / 'normal-dist')], check=True)
    subprocess.run([sys.executable, '-B', str(ROOT / 'tools/m19/verify_distribution.py'),
                    '--dist', str(out / 'normal-dist')], check=True)
    profile = json.loads((ROOT / 'config/m19/loader.json').read_text())
    geometry = json.loads((ROOT / 'config/m19/media.json').read_text())
    epoch = json.loads((ROOT / 'config/m19/host-tooling.json').read_text())['source_date_epoch']
    images = []
    for number in (1, 2):
        shell = out / ('shell-' + str(number))
        subprocess.run([sys.executable, '-B', str(ROOT / 'tools/m19/qa/build_msdos4.py'),
                        '--msdos-repo', str(args.msdos_repo.resolve()),
                        '--emu2-repo', str(args.emu2_repo.resolve()),
                        '--msdos-revision', spec['msdos']['commit'],
                        '--profile', spec['profile'], '--output', str(shell)], check=True)
        # Only the full build just performed supplies DOS applications/media.
        normal = out / 'normal' / ('run-' + str(number))
        _, payloads = inspect((normal / 'media.d88').read_bytes(), geometry)
        payloads = dict(payloads)
        payloads['COMMAND.COM'] = (shell / 'COMMAND.COM').read_bytes()
        config = (ROOT / 'config/m19/CONFIG.SYS').read_text()
        if 'SHELL=' in config or 'VERSION=' in config:
            raise ValueError('normal configuration unexpectedly overrides shell/version')
        config += 'SHELL=A:\\COMMAND.COM A:\\ /P\n'
        payloads['CONFIG.SYS'] = config.replace('\n', '\r\n').encode('ascii')
        payloads['AUTOEXEC.BAT'] = (
            b'@ECHO OFF\r\nSET PATH=A:\\\r\nPROMPT $P$G\r\n'
            b'ECHO MS-DOS 4 COMMAND on FreeDOS - experimental QA only\r\n')
        payloads['MSDOS.LIC'] = (shell / 'msdos/LICENSE').read_bytes()
        payloads['SHELLQA.TXT'] = (
            b'QA only, not the normal FreeCOM distribution. MS-DOS kernel not used.\r\n'
            b'COMMAND source and tools: pinned Microsoft MIT source plus fork profile.\r\n'
            b'No OS/2 file attributes. SYS transfer and hardware NOT QUALIFIED.\r\n')
        media = out / ('media-' + str(number))
        media.mkdir()
        data = compose(payloads, profile, media, epoch)
        _, readback = inspect(data, geometry)
        if readback != payloads:
            raise ValueError('QA media readback mismatch')
        if (media / 'stage1/stage1.bin').read_bytes() != (normal / 'stage1/stage1.bin').read_bytes():
            raise ValueError('QA changed stage-1 loader bytes')
        images.append(data)
    if images[0] != images[1]:
        raise ValueError('independent complete QA builds differ')
    final = out / 'MSDOS4-QA.D88'
    final.write_bytes(images[0])
    record = {'scope': spec['scope'], 'parent_revision': subprocess.check_output(
                  ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'research_source_lock_sha256': digest((ROOT / 'config/m19/msdos4-research.json').read_bytes()),
              'two_complete_builds_equal': True, 'disk_sha256': digest(images[0]),
              'disk_size_bytes': len(images[0]), 'guest': 'NOT RUN', 'hardware': 'NOT RUN'}
    (out / 'qa-build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(str(final))


if __name__ == '__main__':
    main()
