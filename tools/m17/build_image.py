#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the complete M17 candidate twice from committed source exports."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PARENT_INPUTS = ('tools/m17', 'tests/m17', 'config/m17',
                 'manifests/components.lock.json', 'manifests/m17-components.lock.json',
                 'manifests/toolchains.lock.json', 'COPYING', 'LICENSE.md')


def call(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def host_wheel_specs():
    config = json.loads((ROOT / 'config/m17/host-tooling.json').read_text())
    fields = {'package', 'version', 'filename', 'sha256', 'python_tag',
              'abi_tag', 'platform_tag'}
    if (config.get('schema_version') != 2 or
            set(config) != {'schema_version', 'verifier_wheel', 'schema_wheels'}):
        raise ValueError('Pinned M17 host-tooling schema is malformed')
    specs = [config['verifier_wheel'], *config['schema_wheels']]
    expected_schema_wheels = {
        'jsonschema': '4.23.0', 'attrs': '24.3.0',
        'jsonschema-specifications': '2024.10.1',
        'referencing': '0.35.1', 'rpds-py': '0.21.0',
    }
    if ({item.get('package'): item.get('version') for item in specs[1:]} !=
            expected_schema_wheels or len(specs) != 6):
        raise ValueError('Pinned M17 JSON Schema validator dependencies differ')
    for spec in specs:
        if (not isinstance(spec, dict) or set(spec) != fields or
                spec['python_tag'] != '310' or spec['abi_tag'] != 'cp310' or
                spec['platform_tag'] != 'manylinux2014_x86_64' or
                not re.fullmatch(r'[0-9a-f]{64}', spec['sha256']) or
                not spec['filename'].endswith('.whl')):
            raise ValueError('Pinned M17 host wheel identity is malformed')
    if (specs[0]['package'] != 'unicorn' or specs[0]['version'] != '2.1.4' or
            specs[0]['filename'] != 'unicorn-2.1.4-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'):
        raise ValueError('Pinned M17 Unicorn wheel identity is malformed')
    return specs


def component_lock():
    lock = json.loads((ROOT / 'manifests/m17-components.lock.json').read_text())
    if lock.get('schema_version') != 2 or lock.get('milestone') != 'M17':
        raise ValueError('Invalid M17 component lock')
    if lock.get('start_sha') != 'f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4':
        raise ValueError('M17 baseline substitution')
    integration = lock.get('parent_integration')
    expected_integration = {
        'merge_commit': '0852dc543ca9c23829a8059776e2f77072ceb947',
        'preserved_work_parent': '6ef9a327d58e712e8470b5e6746c850c54852bcd',
        'accepted_m16_parent': lock['start_sha'],
    }
    if integration != expected_integration:
        raise ValueError('M17 parent integration provenance differs')
    call('git', 'merge-base', '--is-ancestor', integration['merge_commit'],
         call('git', 'rev-parse', 'HEAD'))
    predecessor = lock.get('predecessor', {})
    expected_predecessor = {
        'milestone': 'M16',
        'publication_tip': lock['start_sha'],
        'status': 'M16 PASS / HANDOFF READY; physical hardware NOT RUN',
        'kernel_component': '7883c8fac11fab20cb467ad0a93c8799f35b565a',
        'freecom_component': '29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e',
        'country_component': '23f189cca3420606eae8723884fa92ccd65eb307',
    }
    if predecessor != expected_predecessor:
        raise ValueError('M17 predecessor acceptance binding is invalid')
    ci = lock.get('predecessor_ci')
    expected_ci = [
        ('M16 isolated source build', 36381203803, 1),
        ('M16 scaffold', 36381203807, 1),
    ]
    if (not isinstance(ci, list) or len(ci) != len(expected_ci) or
            any((item.get('workflow'), item.get('run_id'), item.get('attempt'),
                 item.get('head_sha'), item.get('conclusion')) !=
                (workflow, run_id, attempt, lock['start_sha'], 'success')
                for item, (workflow, run_id, attempt) in zip(ci, expected_ci))):
        raise ValueError('M16 predecessor CI is not bound to the exact accepted head')
    entries = lock['components']
    by_path = {item['path']: item for item in entries}
    if len(entries) != 3 or set(by_path) != {'components/fdkernel', 'components/freecom', 'components/country'}:
        raise ValueError('Invalid M17 component set')
    expected = {
        'fdkernel': ('https://github.com/nakatamaho/fdkernel.git', 'topic/m17-storage-contracts-media-formats'),
        'freecom': ('https://github.com/nakatamaho/freecom_dbcs2.git', 'topic/m16-floppy-formats-console-input'),
        'country': ('https://github.com/FDOS/country.git', 'master'),
    }
    for path, item in by_path.items():
        name = path.split('/')[-1]
        if item['name'] != name or (item['repository'], item['branch']) != expected[name]:
            raise ValueError('M17 source provenance mismatch')
        if not re.fullmatch(r'[0-9a-f]{40}', item['commit']) or not re.fullmatch(r'[0-9a-f]{64}', item['source_archive_sha256']):
            raise ValueError('Invalid M17 source identity')
    kernel = by_path['components/fdkernel']
    expected_parents = ['1527da489528367bb8028a8e9576375d35722f50',
                        '7883c8fac11fab20cb467ad0a93c8799f35b565a']
    if (kernel['commit'] != 'e87e8071c355a99a7f34a8758d4a3368b6523f3d' or
            kernel.get('merge_parents') != expected_parents):
        raise ValueError('M17 kernel integration is not bound to the reviewed M16 merge')
    return by_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/m17-image')
    parser.add_argument('--image', default='freedos-pc88va-m16:local')
    args = parser.parse_args()
    if call('git', 'diff', 'HEAD', '--', '.', ':!components/fdkernel'):
        raise ValueError('Commit parent changes before exporting the build')
    for line in call('git', 'status', '--porcelain', '--untracked-files=all').splitlines():
        path = line[3:].strip()
        if not path.startswith(('components/fdkernel', 'components/freecom',
                                'components/country')):
            raise ValueError('Uncommitted parent input: ' + path)
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
            raise ValueError('Component gitlink differs from the M17 lock: ' + name)
    output = args.output.resolve()
    output.relative_to(ROOT)
    if subprocess.run(['git', 'check-ignore', '-q', str(output / 'probe')], cwd=ROOT).returncode:
        raise ValueError('Build output must be Git-excluded')
    if output.exists():
        raise ValueError('Output already exists; choose a new M17_IMAGE_OUTPUT')
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
            raise ValueError('Component source archive differs from the M17 lock: ' + name)
    # Test-only host dependencies are independently pinned and extracted into
    # network-disabled Linux/amd64 containers for both source builds.
    wheel_specs = host_wheel_specs()
    for spec in wheel_specs:
        subprocess.run([sys.executable, '-m', 'pip', 'download', '--disable-pip-version-check', '--no-cache-dir',
                        '--only-binary=:all:', '--no-deps', '--platform', spec['platform_tag'],
                        '--python-version', spec['python_tag'], '--implementation', 'cp',
                        '--abi', spec['abi_tag'], '--dest', str(inputs),
                        spec['package'] + '==' + spec['version']], check=True)
    wheels = list(inputs.glob('*.whl'))
    if {wheel.name for wheel in wheels} != {spec['filename'] for spec in wheel_specs}:
        raise ValueError('Downloaded M17 host wheel set differs from its lock')
    host_wheel_shas = {}
    for spec in wheel_specs:
        wheel = inputs / spec['filename']
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if digest != spec['sha256']:
            raise ValueError('Downloaded M17 host wheel hash differs: ' + spec['package'])
        host_wheel_shas[spec['package']] = digest
    results = []
    command = 'mkdir -p /work/entry && tar -xf /input/parent.tar -C /work/entry tools/m17/build_image.sh && bash /work/entry/tools/m17/build_image.sh'
    for number in (1, 2):
        cid = call('docker', 'create', '--platform', 'linux/amd64', '--network', 'none',
                   '-e', f'M17_BUILD_PASS={number}', '--entrypoint', 'bash', info['Id'], '-ec', command)
        try:
            subprocess.run(['docker', 'cp', str(inputs) + '/.', cid + ':/input'], check=True)
            with (output / f'build-{number}.log').open('xb') as f:
                try:
                    subprocess.run(['docker', 'start', '-a', cid], stdout=f, stderr=subprocess.STDOUT, check=True)
                except subprocess.CalledProcessError:
                    subprocess.run(['docker', 'cp', cid + ':/work/result', str(output / f'failed-{number}')], check=False)
                    raise
            target = output / f'run-{number}'
            subprocess.run(['docker', 'cp', cid + ':/work/result', str(target)], check=True)
            results.append(json.loads((target / 'artifacts.json').read_text()))
        finally:
            subprocess.run(['docker', 'rm', '-f', cid], check=True, stdout=subprocess.DEVNULL)
    if results[0] != results[1]:
        raise ValueError('Independent clean builds differ')
    media = (output / 'run-1/media.d88').read_bytes()
    (output / 'media.d88').write_bytes(media)
    vaeg_candidate = json.loads((ROOT / 'config/m17/vaeg-candidate.json').read_text())
    if (vaeg_candidate.get('schema_version') != 1 or
            len(vaeg_candidate.get('source', {}).get('commit', '')) != 40 or
            any(len(item.get('executable_sha256', '')) != 64
                for item in vaeg_candidate.get('builds', {}).values())):
        raise ValueError('The pinned M16 VAEG candidate identity is malformed')
    record = {'sources': sources, 'source_archives_sha256': archives, 'toolchain_image': info['Id'],
              'host_wheels_sha256': host_wheel_shas,
              'vaeg_candidate': vaeg_candidate,
              'two_clean_builds_equal': True, 'artifacts': results[0],
              'guest_boot': 'NOT RUN', 'hardware': 'NOT RUN'}
    (output / 'build.json').write_text(json.dumps(record, indent=2)+'\n')
    print('Two complete source builds match: ' + str(output / 'media.d88'))


if __name__ == '__main__':
    main()
