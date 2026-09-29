#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compose separate allocator QA media after a complete current-source build.

The Make target always runs m18-disk first. No distribution D88 or private
media is read as a template. Program payloads come from the two fresh builds.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import build_image
from compose_image import compose

ROOT = Path(__file__).resolve().parents[2]
PROGRAMS = ('LOADER.BIN', 'KERNEL.SYS', 'COMMAND.COM', 'COUNTRY.SYS', 'MEMMAP.EXE')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified_payloads(build, manifest, revisions):
    if (manifest['component_revisions'] != revisions or
            manifest['parent_revision'] != revisions['parent'] or
            manifest['two_independent_clean_builds_equal'] is not True):
        raise ValueError('QA requires a complete two-build result for the current pins')
    if set(manifest['source_archives_sha256']) != set(revisions):
        raise ValueError('QA source archive references are incomplete or unknown')
    for name, expected in manifest['source_archives_sha256'].items():
        if digest((build / 'inputs' / (name + '.tar')).read_bytes()) != expected:
            raise ValueError('QA source archive drift: ' + name)
    payloads = {}
    for run in ('run-1', 'run-2'):
        artifacts = json.loads((build / run / 'artifacts.json').read_text())
        for name in PROGRAMS:
            data = (build / run / name).read_bytes()
            if artifacts[name] != {'sha256': digest(data), 'size_bytes': len(data)}:
                raise ValueError('QA payload artifact drift: ' + name)
            if name in payloads and payloads[name] != data:
                raise ValueError('QA independent payload builds differ: ' + name)
            payloads[name] = data
    return payloads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    _, revisions, lock = build_image.verify_parent_and_components()
    manifest = json.loads((args.dist / 'build-manifest.json').read_text())
    expected = {item['name']: item['source_archive_sha256']
                for item in lock['components']}
    expected['parent'] = digest(subprocess.check_output(
        ['git', 'archive', revisions['parent'], *build_image.PARENT_INPUTS], cwd=ROOT))
    if manifest['source_archives_sha256'] != expected:
        raise ValueError('QA source archives do not match committed public inputs')
    payloads = verified_payloads(args.build, manifest, revisions)
    output = build_image.verify_output_root(args.output, 'QA output')
    # Never overwrite a failed or guest-written candidate.
    output.mkdir(exist_ok=False, parents=True)
    source = ROOT / 'tools/m18/qa/alloc.asm'
    # Use the exact clean build's compiler container for the QA executable.
    subprocess.run([
        'docker', 'run', '--rm', '--network', 'none', '--platform', 'linux/amd64',
        '--entrypoint', 'nasm',
        '--user', '{}:{}'.format(os.getuid(), os.getgid()),
        '-v', str(source.parent) + ':/source:ro',
        '-v', str(output) + ':/output', manifest['toolchain_image'],
        '-f', 'bin', '/source/alloc.asm', '-o', '/output/ALLOC.COM',
    ], check=True)
    payloads['ALLOC.COM'] = (output / 'ALLOC.COM').read_bytes()
    if len(payloads['ALLOC.COM']) >= 0xff00:
        raise ValueError('QA COM image exceeds its segment')
    for name, path in (('CONFIG.SYS', 'config/m18/CONFIG.SYS'), ('COPYING', 'COPYING')):
        payloads[name] = (ROOT / path).read_text(encoding='ascii').replace('\n', '\r\n').encode('ascii')
    payloads['QA.TXT'] = b'QA ONLY: run ALLOC > RESULT.TXT, then MEMMAP /CHECK.\r\n'
    epoch = json.loads((ROOT / 'config/m18/host-tooling.json').read_text())['source_date_epoch']
    profile = json.loads((ROOT / 'config/m18/loader.json').read_text())
    image = compose(payloads, profile, output, epoch)
    # The contiguous stage-2 allocation is identical to the normal disk. Check
    # that the host assembler did not change the already-qualified stage 1.
    if (output / 'stage1/stage1.bin').read_bytes() != (args.build / 'run-1/stage1/stage1.bin').read_bytes():
        raise ValueError('QA stage-1 bytes differ from the pinned source build')
    record = {'scope': 'QA ONLY; not the normal distribution',
              'parent_revision': revisions['parent'],
              'component_revisions': revisions,
              'toolchain_image': manifest['toolchain_image'],
              'assembler_source_sha256': digest(source.read_bytes()),
              'probe_sha256': digest(payloads['ALLOC.COM']),
              'image_sha256': digest(image), 'image_size': len(image),
              'guest_result': 'NOT RUN'}
    (output / 'qa-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print(str(output / 'media.d88') + ' SHA-256 ' + digest(image))


if __name__ == '__main__':
    main()
