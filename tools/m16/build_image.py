#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build a complete M16 disk twice from committed source exports."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PARENT_INPUTS = ('tools/m16', 'tests/m16', 'config/m16',
                 'manifests/components.lock.json', 'manifests/m16-components.lock.json',
                 'manifests/toolchains.lock.json', 'COPYING', 'LICENSE.md')


def call(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def verifier_wheel_spec():
    config = json.loads((ROOT / 'config/m16/host-tooling.json').read_text())
    expected = {'package', 'version', 'filename', 'sha256', 'python_tag',
                'abi_tag', 'platform_tag'}
    spec = config.get('verifier_wheel')
    if (config.get('schema_version') != 1 or not isinstance(spec, dict) or
            set(spec) != expected or spec['package'] != 'unicorn' or
            spec['version'] != '2.1.4' or
            spec['python_tag'] != '310' or spec['abi_tag'] != 'cp310' or
            spec['platform_tag'] != 'manylinux2014_x86_64' or
            not re.fullmatch(r'[0-9a-f]{64}', spec['sha256']) or
            not spec['filename'].endswith('.whl')):
        raise ValueError('Pinned M16 verifier wheel identity is malformed')
    return spec


def component_lock():
    lock = json.loads((ROOT / 'manifests/m16-components.lock.json').read_text())
    if lock.get('schema_version') != 1 or lock.get('milestone') != 'M16' or lock.get('status') != 'current-m16':
        raise ValueError('M16 component lock schema or status is invalid')
    expected_history = lock.get('historical_components_lock', {})
    if expected_history != {
            'path': 'manifests/components.lock.json',
            'sha256': '440e481b28c740875489a6953a246ce5370c44074053c7aad3f80e79ec40c19c'}:
        raise ValueError('M16 historical component lock reference is invalid')
    history_sha = hashlib.sha256((ROOT / expected_history['path']).read_bytes()).hexdigest()
    if history_sha != expected_history.get('sha256'):
        raise ValueError('M16 historical component lock identity differs')
    expected_control = {
        'parent_commit': '1af9974700cd4dd1164cc0df56cc062925376148',
        'components': {
            'components/country': '23f189cca3420606eae8723884fa92ccd65eb307',
            'components/fdkernel': 'd8dbbf7111f86ea4800daeac84ac53ba601aaf32',
            'components/freecom': '9cf57b28abf1d98fab7655fb811375a2aa16c6d9',
        },
    }
    if lock.get('m15_control') != expected_control:
        raise ValueError('M16 lock does not preserve the exact M15 control')
    for path, commit in expected_control['components'].items():
        if call('git', 'rev-parse', f"{expected_control['parent_commit']}:{path}") != commit:
            raise ValueError('M15 control component identity differs: ' + path)
    entries = lock.get('components')
    if not isinstance(entries, list) or len(entries) != 3:
        raise ValueError('M16 component lock must contain exactly three components')
    by_path = {item.get('path'): item for item in entries if isinstance(item, dict)}
    if set(by_path) != {'components/fdkernel', 'components/freecom', 'components/country'}:
        raise ValueError('M16 component path set is invalid')
    expected = {
        'components/fdkernel': ('fdkernel', 'https://github.com/nakatamaho/fdkernel.git',
                                'topic/m16-floppy-formats-console-input',
                                expected_control['components']['components/fdkernel']),
        'components/freecom': ('freecom', 'https://github.com/nakatamaho/freecom_dbcs2.git',
                               'topic/m16-floppy-formats-console-input',
                               expected_control['components']['components/freecom']),
        'components/country': ('country', 'https://github.com/FDOS/country.git', 'master', None),
    }
    for path, (name, repository, branch, parent) in expected.items():
        item = by_path[path]
        if (item.get('name') != name or item.get('repository') != repository or
                item.get('branch') != branch or item.get('parent_commit') != parent or
                not re.fullmatch(r'[0-9a-f]{40}', str(item.get('commit', ''))) or
                not re.fullmatch(r'[0-9a-f]{64}', str(item.get('source_archive_sha256', '')))):
            raise ValueError('M16 component provenance record is invalid: ' + path)
    return by_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/m16-image')
    parser.add_argument('--image', default='freedos-pc88va-m16:local')
    parser.add_argument('--boot-profile', default='2hd-1280')
    args = parser.parse_args()
    if call('git', 'diff', 'HEAD', '--', '.', ':!components/fdkernel'):
        raise ValueError('Commit parent changes before exporting the build')
    locked_components = component_lock()
    sources = {'parent': call('git', 'rev-parse', 'HEAD')}
    for name in ('fdkernel', 'freecom', 'country'):
        path = 'components/' + name
        sources[name] = call('git', 'rev-parse', 'HEAD:' + path)
        if call('git', '-C', path, 'rev-parse', 'HEAD') != sources[name]:
            raise ValueError('Component checkout differs from parent gitlink: ' + name)
        if call('git', '-C', path, 'status', '--porcelain', '--untracked-files=no'):
            raise ValueError('Component tracked source is dirty: ' + name)
        if locked_components[path].get('commit') != sources[name]:
            raise ValueError('Component gitlink differs from the M16 lock: ' + name)
    output = args.output.resolve()
    output.relative_to(ROOT)
    if subprocess.run(['git', 'check-ignore', '-q', str(output / 'probe')], cwd=ROOT).returncode:
        raise ValueError('Build output must be Git-excluded')
    if output.exists():
        raise ValueError('Output already exists; choose a new M16_IMAGE_OUTPUT')
    info = json.loads(call('docker', 'image', 'inspect', args.image))[0]
    if (info['Os'], info['Architecture']) != ('linux', 'amd64'):
        raise ValueError('The pinned Linux/amd64 toolchain image is required')
    output.mkdir(parents=True)
    inputs = output / 'inputs'
    inputs.mkdir()
    archives = {}
    for name, sha in sources.items():
        repo = ROOT if name == 'parent' else ROOT / 'components' / name
        archive = inputs / (name + '.tar')
        with archive.open('xb') as f:
            command = ['git', '-C', str(repo), 'archive', sha]
            if name == 'parent':
                command.extend(PARENT_INPUTS)
            subprocess.run(command, stdout=f, check=True)
        archives[name] = hashlib.sha256(archive.read_bytes()).hexdigest()
        if name != 'parent' and archives[name] != locked_components[f'components/{name}'].get('source_archive_sha256'):
            raise ValueError('Component source archive differs from the M16 lock: ' + name)
    # This verifier dependency is separate from the guest toolchain. Fetch a
    # pinned Linux wheel once; both build containers remain network-disabled.
    verifier = verifier_wheel_spec()
    subprocess.run([sys.executable, '-m', 'pip', 'download', '--disable-pip-version-check', '--no-cache-dir',
                    '--only-binary=:all:', '--no-deps', '--platform', verifier['platform_tag'],
                    '--python-version', verifier['python_tag'], '--implementation', 'cp',
                    '--abi', verifier['abi_tag'], '--dest', str(inputs),
                    verifier['package'] + '==' + verifier['version']], check=True)
    wheels = list(inputs.glob('unicorn-*.whl'))
    if len(wheels) != 1 or wheels[0].name != verifier['filename']:
        raise ValueError('Downloaded M16 verifier wheel name differs from its lock')
    wheel = wheels[0]
    wheel_sha256 = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if wheel_sha256 != verifier['sha256']:
        raise ValueError('Downloaded M16 verifier wheel hash differs from its lock')
    results = []
    command = ('mkdir -p /work/entry && tar -xf /input/parent.tar -C /work/entry tools/m16/build_image.sh '
               '&& bash /work/entry/tools/m16/build_image.sh')
    for number in (1, 2):
        cid = call('docker', 'create', '--platform', 'linux/amd64', '--network', 'none',
                   '-e', f'M16_BUILD_PASS={number}', '-e', f'M16_BOOT_PROFILE={args.boot_profile}',
                   '--entrypoint', 'bash', info['Id'], '-ec', command)
        try:
            subprocess.run(['docker', 'cp', str(inputs) + '/.', cid + ':/input'], check=True)
            with (output / f'build-{number}.log').open('xb') as f:
                subprocess.run(['docker', 'start', '-a', cid], stdout=f, stderr=subprocess.STDOUT, check=True)
            target = output / f'run-{number}'
            subprocess.run(['docker', 'cp', cid + ':/work/result', str(target)], check=True)
            results.append(json.loads((target / 'artifacts.json').read_text()))
        finally:
            subprocess.run(['docker', 'rm', '-f', cid], check=True, stdout=subprocess.DEVNULL)
    if results[0] != results[1]:
        raise ValueError('Independent clean builds differ')
    media = (output / 'run-1/media.d88').read_bytes()
    (output / 'media.d88').write_bytes(media)
    vaeg_candidate = json.loads((ROOT / 'config/m16/vaeg-candidate.json').read_text())
    if (vaeg_candidate.get('schema_version') != 1 or
            len(vaeg_candidate.get('source', {}).get('commit', '')) != 40 or
            any(len(item.get('executable_sha256', '')) != 64
                for item in vaeg_candidate.get('builds', {}).values())):
        raise ValueError('The pinned M16 VAEG candidate identity is malformed')
    record = {'sources': sources, 'source_archives_sha256': archives, 'toolchain_image': info['Id'],
              'verifier_wheel_sha256': wheel_sha256,
              'vaeg_candidate': vaeg_candidate,
              'two_clean_builds_equal': True, 'artifacts': results[0],
              'guest_boot': 'NOT RUN', 'hardware': 'NOT RUN'}
    (output / 'build.json').write_text(json.dumps(record, indent=2)+'\n')
    print('Two complete source builds match: ' + str(output / 'media.d88'))


if __name__ == '__main__':
    main()
