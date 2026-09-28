#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed verification of one complete M17 clean double-build."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
import struct

ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_floppy_media import profile_payload, profile_spec
from build_image import PARENT_INPUTS, component_lock, host_wheel_specs
from contracts import ContractError, load as load_storage_profiles
from inspect_storage import _verify_manifest
from media import derive_layout, inspect as inspect_d88
from toolchain import verify_image

HEX64 = re.compile(r'^[0-9a-f]{64}$')
IMAGE_ID = re.compile(r'^sha256:[0-9a-f]{64}$')
BUILD_FIELDS = {
    'sources', 'source_archives_sha256', 'toolchain_image',
    'host_wheels_sha256', 'vaeg_candidate', 'two_clean_builds_equal',
    'artifacts', 'guest_boot', 'hardware',
}
SOURCE_NAMES = {'parent', 'fdkernel', 'freecom', 'country'}
TEST_SUITES = (
    'storage', 'config-qa', 'm13-memory-placement', 'm13-carrier-tail',
    'floppy-media', 'loader-builder', 'loadseg-contract',
    'freecom-input-source', 'dos-input-probe', 'dos-freecom-editor',
    'dos-repeat-probe', 'acceptance',
)
LINKED_GATES = (
    'LINKED_PLATFORM_FRAME_AND_CON_CONTRACT_OK',
    'LINKED_INIT_FORMATTER_SEPARATE_STACK_OK',
    'INIT_MODEL_BANNER_BRANCHES_AND_BANK_RESTORE_OK',
    'RESIDENT_ONE_SECTOR_BUFFER_READ_WRITE_BOUNDS_OK',
    'REAL_SPLIT_BRIDGE_AND_ALL_FINAL_FIXUPS_OK',
)
CONFIG_QA_FIELDS = {
    'name', 'image', 'size_bytes', 'sha256', 'config_source',
    'config_sha256', 'fdconfig_source', 'fdconfig_sha256',
    'loader_loadseg', 'device_driver', 'expected_config_file',
}
FLOPPY_ROW_FIELDS = {
    'guest_media_id', 'geometry', 'payload_bytes', 'raw_capacity_bytes',
    'd88_size', 'd88_sha256', 'filesystem',
}


class AcceptanceError(ValueError):
    """A source, build record, output, or acceptance proof is invalid."""


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise AcceptanceError('duplicate JSON key: ' + key)
        value[key] = item
    return value


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise AcceptanceError('missing or unsafe JSON input: ' + str(path))
    try:
        return json.loads(path.read_text(encoding='utf-8'),
                          object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AcceptanceError('invalid JSON input ' + str(path) + ': ' + str(error)) from error


def _object(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise AcceptanceError(label + ': unknown or missing fields')


def _digest(value, label):
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise AcceptanceError(label + ': malformed SHA-256')


def _hash_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def validate_predecessor_ci(claims, start_sha):
    """Reject stale, substituted, malformed, or extended predecessor CI claims."""
    if not isinstance(start_sha, str) or not re.fullmatch(r'[0-9a-f]{40}', start_sha):
        raise AcceptanceError('M16 START_SHA is malformed')
    expected = [
        {
            'workflow': 'M16 isolated source build',
            'run_id': 36381203803,
            'attempt': 1,
            'head_sha': start_sha,
            'conclusion': 'success',
        },
        {
            'workflow': 'M16 scaffold',
            'run_id': 36381203807,
            'attempt': 1,
            'head_sha': start_sha,
            'conclusion': 'success',
        },
    ]
    if claims != expected:
        raise AcceptanceError('M16 predecessor CI claims are stale or incomplete')


def validate_m17_lock(lock, root=ROOT):
    """Validate the exact M17 provenance-record shape and historical bindings."""
    _object(lock, {
        'components', 'historical_components_lock', 'm15_control', 'milestone',
        'parent_integration', 'predecessor', 'predecessor_ci', 'schema_version',
        'start_sha', 'status',
    }, 'M17 component lock')
    if (type(lock['schema_version']) is not int or lock['schema_version'] != 2 or
            lock['milestone'] != 'M17' or
            lock['start_sha'] != 'f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4' or
            lock['status'] != 'M17 PASS (CONTRACTS/FIXTURES); HANDOFF READY'):
        raise AcceptanceError('M17 component lock has a stale milestone binding')
    historic = lock['historical_components_lock']
    _object(historic, {'path', 'sha256'}, 'historical component lock binding')
    if historic['path'] != 'manifests/components.lock.json':
        raise AcceptanceError('historical component lock path changed')
    _digest(historic['sha256'], 'historical component lock')
    if historic['sha256'] != _hash_file(Path(root) / historic['path']):
        raise AcceptanceError('historical component lock digest drift')

    expected_m15 = {
        'components': {
            'components/country': '23f189cca3420606eae8723884fa92ccd65eb307',
            'components/fdkernel': 'd8dbbf7111f86ea4800daeac84ac53ba601aaf32',
            'components/freecom': '9cf57b28abf1d98fab7655fb811375a2aa16c6d9',
        },
        'parent_commit': '1af9974700cd4dd1164cc0df56cc062925376148',
    }
    if lock['m15_control'] != expected_m15:
        raise AcceptanceError('M17 M15 regression-control binding changed')
    expected_integration = {
        'merge_commit': '0852dc543ca9c23829a8059776e2f77072ceb947',
        'preserved_work_parent': '6ef9a327d58e712e8470b5e6746c850c54852bcd',
        'accepted_m16_parent': lock['start_sha'],
    }
    if lock['parent_integration'] != expected_integration:
        raise AcceptanceError('M17 parent integration binding changed')
    expected_predecessor = {
        'milestone': 'M16',
        'publication_tip': lock['start_sha'],
        'status': 'M16 PASS / HANDOFF READY; physical hardware NOT RUN',
        'kernel_component': '7883c8fac11fab20cb467ad0a93c8799f35b565a',
        'freecom_component': '29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e',
        'country_component': '23f189cca3420606eae8723884fa92ccd65eb307',
    }
    if lock['predecessor'] != expected_predecessor:
        raise AcceptanceError('M17 predecessor identity or acceptance state changed')
    validate_predecessor_ci(lock['predecessor_ci'], lock['start_sha'])

    component_fields = {
        'country': {'branch', 'commit', 'name', 'parent_commit', 'path',
                    'repository', 'role', 'source_archive_sha256'},
        'freecom': {'branch', 'commit', 'name', 'parent_commit', 'path',
                    'repository', 'role', 'source_archive_sha256', 'upstream'},
        'fdkernel': {'branch', 'commit', 'merge_parents', 'name', 'parent_commit',
                     'path', 'repository', 'role', 'source_archive_sha256', 'upstream'},
    }
    rows = lock['components']
    if not isinstance(rows, list) or len(rows) != 3:
        raise AcceptanceError('M17 component lock must bind exactly three components')
    names = set()
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('name'), str) or
                row.get('name') not in component_fields):
            raise AcceptanceError('M17 component lock has an unknown component')
        name = row['name']
        _object(row, component_fields[name], 'M17 component ' + name)
        names.add(name)
        if row['path'] != 'components/' + name:
            raise AcceptanceError('M17 component path/name mismatch: ' + name)
        if (not isinstance(row['commit'], str) or
                not re.fullmatch(r'[0-9a-f]{40}', row['commit'])):
            raise AcceptanceError('M17 component commit is malformed: ' + name)
        if row['parent_commit'] is not None and (
                not isinstance(row['parent_commit'], str) or
                not re.fullmatch(r'[0-9a-f]{40}', row['parent_commit'])):
            raise AcceptanceError('M17 component parent commit is malformed: ' + name)
        _digest(row['source_archive_sha256'], 'M17 component archive ' + name)
        if name == 'fdkernel':
            if (not isinstance(row['merge_parents'], list) or
                    len(row['merge_parents']) != 2 or
                    any(not isinstance(sha, str) or
                        not re.fullmatch(r'[0-9a-f]{40}', sha)
                        for sha in row['merge_parents'])):
                raise AcceptanceError('M17 kernel merge-parent identities are malformed')
    if names != set(component_fields):
        raise AcceptanceError('M17 component lock has an incomplete component set')


def validate_build_record(record):
    _object(record, BUILD_FIELDS, 'build.json')
    if not isinstance(record['sources'], dict) or set(record['sources']) != SOURCE_NAMES:
        raise AcceptanceError('build source identity set is incomplete')
    for name, value in record['sources'].items():
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value):
            raise AcceptanceError('malformed source identity: ' + name)
    if (not isinstance(record['source_archives_sha256'], dict) or
            set(record['source_archives_sha256']) != SOURCE_NAMES):
        raise AcceptanceError('source archive identity set is incomplete')
    for name, value in record['source_archives_sha256'].items():
        _digest(value, 'source archive ' + name)
    if not isinstance(record['toolchain_image'], str) or not IMAGE_ID.fullmatch(record['toolchain_image']):
        raise AcceptanceError('toolchain image identity is malformed')
    if (not isinstance(record['host_wheels_sha256'], dict) or
            set(record['host_wheels_sha256']) != {
                'unicorn', 'jsonschema', 'attrs', 'jsonschema-specifications',
                'referencing', 'rpds-py'}):
        raise AcceptanceError('pinned host wheel identity set is incomplete')
    for name, value in record['host_wheels_sha256'].items():
        _digest(value, 'host wheel ' + name)
    if type(record['two_clean_builds_equal']) is not bool or not record['two_clean_builds_equal']:
        raise AcceptanceError('two independent clean builds are not affirmed')
    if record['guest_boot'] != 'NOT RUN' or record['hardware'] != 'NOT RUN':
        raise AcceptanceError('M17 host build must not imply guest or hardware qualification')
    if not isinstance(record['artifacts'], dict) or not record['artifacts']:
        raise AcceptanceError('build artifact manifest is missing')
    if not isinstance(record['vaeg_candidate'], dict):
        raise AcceptanceError('pinned M16 VAEG candidate record is malformed')


def _relative_path(value, label):
    if (not isinstance(value, str) or not value or '\\' in value or
            not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', value)):
        raise AcceptanceError(label + ': unsafe relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ('', '.', '..') for part in path.parts):
        raise AcceptanceError(label + ': unsafe relative path')
    return path


def _safe_file(root, relative, label):
    relative_path = _relative_path(relative, label)
    root = Path(root)
    target = root.joinpath(*relative_path.parts)
    current = root
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            raise AcceptanceError(label + ': symlink is not allowed')
    if not target.is_file():
        raise AcceptanceError(label + ': required file is missing: ' + relative)
    if root.resolve() not in target.resolve().parents:
        raise AcceptanceError(label + ': path escapes its root')
    return target


def _tree_files(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise AcceptanceError('build result directory is missing or unsafe')
    found = set()
    for directory, dirs, files in os.walk(root, topdown=True, followlinks=False):
        directory = Path(directory)
        for name in dirs:
            if (directory / name).is_symlink():
                raise AcceptanceError('build output contains a symlink directory')
        for name in files:
            path = directory / name
            if path.is_symlink() or not path.is_file():
                raise AcceptanceError('build output contains an unsafe file')
            found.add(path.relative_to(root).as_posix())
    return found


def validate_artifact_tree(directory, records):
    """Bind every declared artifact to bytes and reject missing/extra files."""
    if not isinstance(records, dict) or not records:
        raise AcceptanceError('empty artifact manifest')
    for relative, item in records.items():
        _relative_path(relative, 'artifact path')
        _object(item, {'size', 'sha256'}, 'artifact record ' + relative)
        if type(item['size']) is not int or item['size'] < 0:
            raise AcceptanceError('malformed artifact size: ' + relative)
        _digest(item['sha256'], 'artifact ' + relative)
    root = Path(directory)
    actual = _tree_files(root)
    actual.discard('artifacts.json')
    if actual != set(records):
        missing = sorted(set(records) - actual)
        extra = sorted(actual - set(records))
        raise AcceptanceError(f'artifact tree differs from manifest; missing={missing}, extra={extra}')
    for relative, item in records.items():
        path = _safe_file(root, relative, 'artifact')
        if path.stat().st_size != item['size'] or _hash_file(path) != item['sha256']:
            raise AcceptanceError('artifact bytes differ from manifest: ' + relative)


def verify_build_log(path, tests_required=True):
    try:
        text = Path(path).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        raise AcceptanceError('cannot read clean-build log: ' + str(error)) from error
    starts = re.findall(r'^M17_TEST_BEGIN ([a-z0-9-]+)$', text, re.MULTILINE)
    passes = re.findall(r'^M17_TEST_PASS ([a-z0-9-]+)$', text, re.MULTILINE)
    expected_suites = list(TEST_SUITES) if tests_required else []
    if starts != expected_suites or passes != expected_suites:
        raise AcceptanceError('clean-build log has missing, stale, duplicated, or reordered test results')
    required = (
        'M17 build export is isolated from other milestones',
        'M17 reviewed sources match pinned kernel',
        *LINKED_GATES,
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise AcceptanceError('clean-build log omits required gates: ' + ', '.join(missing))
    if re.search(r'^FAILED(?: \(|$)', text, re.MULTILINE):
        raise AcceptanceError('clean-build log contains a failing test summary')


def _git_output(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def is_documentation_only_publication_path(path):
    """Allow report/docs publication without rebuilding qualified artifacts."""
    return path.startswith('docs/') or path == 'tools/m17/README.md'


def _archive_digest(repo, commit, paths=()):
    command = ['git', '-C', str(repo), 'archive', commit, *paths]
    digest = hashlib.sha256()
    with tempfile.TemporaryFile() as output:
        subprocess.run(command, stdout=output, check=True)
        output.seek(0)
        for block in iter(lambda: output.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_source_inputs(build_dir, root, record):
    root = Path(root).resolve()
    lock_document = read_json(root / 'manifests/m17-components.lock.json')
    validate_m17_lock(lock_document, root)
    locked_by_path = component_lock()

    validate_build_record(record)
    head = _git_output(root, 'rev-parse', 'HEAD')
    build_parent = record['sources']['parent']
    if subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor',
                       build_parent, head]).returncode:
        raise AcceptanceError('qualified parent source is not an ancestor of the current publication tip')
    changed = _git_output(root, 'diff', '--name-only', build_parent + '..' + head).splitlines()
    if any(not is_documentation_only_publication_path(path) for path in changed):
        raise AcceptanceError('source changed after clean build outside documentation-only publication')

    sources = {'parent': build_parent}
    for name in ('fdkernel', 'freecom', 'country'):
        path = root / 'components' / name
        gitlink = _git_output(root, 'rev-parse', 'HEAD:components/' + name)
        qualified_gitlink = _git_output(root, 'rev-parse',
                                        build_parent + ':components/' + name)
        checkout = _git_output(path, 'rev-parse', 'HEAD')
        if checkout != gitlink or gitlink != qualified_gitlink:
            raise AcceptanceError('component checkout differs from qualified/current gitlinks: ' + name)
        if _git_output(path, 'status', '--porcelain', '--untracked-files=no'):
            raise AcceptanceError('component tracked source is dirty: ' + name)
        sources[name] = gitlink

    if record['sources'] != sources:
        raise AcceptanceError('build source SHAs do not match the exact qualified gitlinks')
    status = _git_output(root, 'status', '--porcelain', '--untracked-files=all')
    if status:
        raise AcceptanceError('parent worktree is not clean at acceptance time')

    # component_lock() has already validated the complete provenance table.
    repos = {
        'parent': (root, PARENT_INPUTS),
        'fdkernel': (root / 'components/fdkernel', ()),
        'freecom': (root / 'components/freecom', ()),
        'country': (root / 'components/country', ()),
    }
    archive_names = {name + '.tar' for name in SOURCE_NAMES}
    wheel_specs = host_wheel_specs()
    input_root = Path(build_dir) / 'inputs'
    if input_root.is_symlink() or not input_root.is_dir():
        raise AcceptanceError('build inputs directory is missing or unsafe')
    input_files = set()
    for path in input_root.iterdir():
        if path.is_symlink() or not path.is_file():
            raise AcceptanceError('build inputs contain a directory or symlink')
        input_files.add(path.name)
    expected_inputs = archive_names | {item['filename'] for item in wheel_specs}
    if input_files != expected_inputs:
        raise AcceptanceError('build inputs differ from the exact pinned source/wheel set')

    if set(record['source_archives_sha256']) != SOURCE_NAMES:
        raise AcceptanceError('source archive records are incomplete')
    for name, (repo, paths) in repos.items():
        commit = sources[name]
        recorded = record['source_archives_sha256'][name]
        archive_path = input_root / (name + '.tar')
        actual = _hash_file(archive_path)
        expected = _archive_digest(repo, commit, paths)
        if actual != recorded or actual != expected:
            raise AcceptanceError('source archive is stale or differs from exact source: ' + name)
        if name != 'parent':
            lock_entry = locked_by_path['components/' + name]
            if commit != lock_entry['commit'] or actual != lock_entry['source_archive_sha256']:
                raise AcceptanceError('component archive differs from public M17 lock: ' + name)

    wheel_hashes = {}
    for spec in wheel_specs:
        path = input_root / spec['filename']
        digest = _hash_file(path)
        if digest != spec['sha256']:
            raise AcceptanceError('pinned host dependency digest drift: ' + spec['package'])
        wheel_hashes[spec['package']] = digest
    if record['host_wheels_sha256'] != wheel_hashes:
        raise AcceptanceError('build host-wheel binding differs from pinned inputs')

    candidate = read_json(root / 'config/m17/vaeg-candidate.json')
    if record['vaeg_candidate'] != candidate:
        raise AcceptanceError('VAEG candidate identity differs from the M16 lock')
    if (candidate.get('schema_version') != 1 or
            set(candidate) != {'schema_version', 'source', 'builds'} or
            set(candidate.get('source', {})) != {'repository', 'branch', 'commit'} or
            not re.fullmatch(r'[0-9a-f]{40}', candidate['source'].get('commit', '')) or
            set(candidate.get('builds', {})) != {'linux', 'windows_mingw64'}):
        raise AcceptanceError('pinned VAEG candidate record is malformed')
    for item in candidate['builds'].values():
        if not isinstance(item, dict) or not HEX64.fullmatch(item.get('executable_sha256', '')):
            raise AcceptanceError('pinned VAEG executable hash is malformed')

    toolchains = read_json(root / 'manifests/toolchains.lock.json')
    image = record['toolchain_image']
    try:
        checked_image = verify_image(image, toolchains['canonical'])
    except (OSError, subprocess.CalledProcessError, KeyError, ValueError) as error:
        raise AcceptanceError('pinned Linux/amd64 toolchain verification failed: ' + str(error)) from error
    if checked_image != image:
        raise AcceptanceError('toolchain image identity changed during verification')


def _media_spec(root):
    spec = read_json(Path(root) / 'config/m17/media.json')
    spec['d88']['disk_name'] = 'FDOS-PC88VA-M17'
    spec['image']['volume_label'] = 'PC88VA-M17'
    return spec


def _base_payloads(run_dir, root):
    names = (
        'KERNEL.SYS', 'LOADER.BIN', 'COMMAND.COM', 'COUNTRY.SYS', 'SYSVA.EXE',
        'COMPROBE.COM', 'CFGSTATE.COM', 'CFGMEM.COM', 'CFGPROBE.COM',
        'CFGDEV.SYS', 'CFGNONE.SYS', 'DOSINPUT.COM', 'DOSREPT.COM', 'MZPROBE.EXE',
    )
    payloads = {name: _safe_file(run_dir, name, 'build payload').read_bytes()
                for name in names}
    config = (Path(root) / 'config/m17/CONFIG.SYS').read_text(encoding='ascii')
    payloads['CONFIG.SYS'] = config.replace('\n', '\r\n').encode('ascii')
    payloads['SYS.ID'] = b'M16SOURCE\r\n'
    payloads['TYPEA.TXT'] = b'M13-TYPE-A!\r\n'
    payloads['TYPEB.TXT'] = b'M13-TYPE-B!\r\n'
    payloads['COMDATA.TXT'] = b'M13-COM-DATA\r\n'
    return payloads


def _expected_allocations(payloads, spec):
    layout = derive_layout(spec)
    bps = spec['geometry']['bytes_per_sector']
    names = ['LOADER.BIN'] + sorted(set(payloads) - {'LOADER.BIN'})
    cluster = 2
    allocations = {}
    for name in names:
        count = (len(payloads[name]) + bps - 1) // bps
        if cluster + count > layout['data_clusters'] + 2:
            raise AcceptanceError('source-built payloads exceed the declared FAT12 volume')
        allocations[name] = {
            'first_lba': layout['first_data_sector'] + cluster - 2,
            'sector_count': count,
            'file_size': len(payloads[name]),
        }
        cluster += count
    return allocations


def _verify_d88_payloads(path, spec, payloads, label):
    try:
        report, actual = inspect_d88(Path(path).read_bytes(), spec)
    except (OSError, ValueError, KeyError, struct.error) as error:
        raise AcceptanceError(label + ': candidate D88 is invalid: ' + str(error)) from error
    if actual != payloads:
        raise AcceptanceError(label + ': D88 payloads differ from exact source-built inputs')
    return report


def verify_distribution_media(run_dir, root):
    run_dir, root = Path(run_dir), Path(root)
    spec = _media_spec(root)
    payloads = _base_payloads(run_dir, root)
    report = _verify_d88_payloads(run_dir / 'media.d88', spec, payloads,
                                  'distribution candidate')
    media_manifest = read_json(run_dir / 'media.json')
    _object(media_manifest, {'allocations', 'filesystem'}, 'media.json')
    if (media_manifest['filesystem'] != report or
            media_manifest['allocations'] != _expected_allocations(payloads, spec)):
        raise AcceptanceError('candidate D88 inspector report or allocation map differs from media.json')

    qa_config_path = root / 'config/m17/config-qa.json'
    qa_config = read_json(qa_config_path)
    _object(qa_config, {'schema_version', 'profiles'}, 'CONFIG QA profiles')
    if type(qa_config['schema_version']) is not int or qa_config['schema_version'] != 1:
        raise AcceptanceError('unsupported CONFIG QA schema version')
    rows = qa_config['profiles']
    expected_names = {
        'baseline-config', 'fdconfig-precedence', 'character-init',
        'zero-unit-init', 'loadseg-2000',
    }
    if (not isinstance(rows, list) or len(rows) != len(expected_names) or
            {row.get('name') for row in rows if isinstance(row, dict)} != expected_names):
        raise AcceptanceError('CONFIG QA profile set is incomplete or duplicated')
    qa_manifest = read_json(run_dir / 'config-qa/manifest.json')
    _object(qa_manifest, {'schema_version', 'profile_sha256', 'profiles'},
            'CONFIG QA manifest')
    if (type(qa_manifest['schema_version']) is not int or
            qa_manifest['schema_version'] != 1 or
            qa_manifest['profile_sha256'] != _hash_file(qa_config_path) or
            not isinstance(qa_manifest['profiles'], list) or
            len(qa_manifest['profiles']) != len(rows)):
        raise AcceptanceError('CONFIG QA manifest is stale or incomplete')
    for source_row, built_row in zip(rows, qa_manifest['profiles']):
        _object(source_row, {
            'name', 'config_source', 'fdconfig_source', 'loadseg',
            'device_driver', 'expected_config_file'}, 'CONFIG QA source profile')
        _object(built_row, CONFIG_QA_FIELDS, 'CONFIG QA build record')
        for field in ('name', 'config_source', 'fdconfig_source', 'loadseg',
                      'device_driver', 'expected_config_file'):
            target_field = 'loader_loadseg' if field == 'loadseg' else field
            if source_row[field] != built_row[target_field]:
                raise AcceptanceError('CONFIG QA profile binding differs: ' + source_row['name'])
        if source_row['config_source'] not in {'CONFIG.SYS', 'CONFIG.loadseg-2000.SYS'}:
            raise AcceptanceError('CONFIG QA source is outside the committed M17 profiles')
        if source_row['fdconfig_source'] not in {
                None, 'FDCONFIG.control', 'FDCONFIG.character', 'FDCONFIG.zero-units'}:
            raise AcceptanceError('FDCONFIG QA source is outside the committed M17 profiles')
        if source_row['loadseg'] not in {'1000', '2000'}:
            raise AcceptanceError('CONFIG QA LOADSEG is outside the selected policy')
        if (source_row['expected_config_file'] !=
                ('FDCONFIG.SYS' if source_row['fdconfig_source'] else 'CONFIG.SYS')):
            raise AcceptanceError('CONFIG QA precedence expectation is inconsistent')
        config_path = root / 'config/m17' / source_row['config_source']
        config_text = config_path.read_text(encoding='ascii')
        match = re.search(r'^PC88VA_LOADSEG=([0-9A-Fa-f]+)h?\s*$', config_text,
                          flags=re.MULTILINE)
        if not match or match.group(1).upper() != source_row['loadseg']:
            raise AcceptanceError('CONFIG QA LOADSEG differs from its committed source')
        config_bytes = config_text.replace('\n', '\r\n').encode('ascii')
        if built_row['config_sha256'] != hashlib.sha256(config_bytes).hexdigest():
            raise AcceptanceError('CONFIG QA CONFIG.SYS digest drift: ' + source_row['name'])
        qa_payloads = dict(payloads)
        qa_payloads['CONFIG.SYS'] = config_bytes
        if source_row['fdconfig_source'] is not None:
            fdconfig_path = root / 'config/m17' / source_row['fdconfig_source']
            fdconfig = fdconfig_path.read_text(encoding='ascii')
            fdconfig_bytes = fdconfig.replace('\n', '\r\n').encode('ascii')
            fdigest = hashlib.sha256(fdconfig_bytes).hexdigest()
            qa_payloads['FDCONFIG.SYS'] = fdconfig_bytes
        else:
            fdigest = None
        if built_row['fdconfig_sha256'] != fdigest:
            raise AcceptanceError('CONFIG QA FDCONFIG.SYS digest drift: ' + source_row['name'])
        if (built_row['image'] != source_row['name'] + '/media.d88' or
                type(built_row['size_bytes']) is not int or built_row['size_bytes'] <= 0 or
                not isinstance(built_row['sha256'], str) or
                not HEX64.fullmatch(built_row['sha256'])):
            raise AcceptanceError('CONFIG QA image size/hash/path is malformed: ' + source_row['name'])
        image = _safe_file(run_dir / 'config-qa', built_row['image'], 'CONFIG QA image')
        if (image.stat().st_size != built_row['size_bytes'] or
                _hash_file(image) != built_row['sha256']):
            raise AcceptanceError('CONFIG QA image digest drift: ' + source_row['name'])
        qa_report = _verify_d88_payloads(image, spec, qa_payloads,
                                         'CONFIG QA ' + source_row['name'])
        qa_media_manifest = read_json(image.parent / 'media.json')
        _object(qa_media_manifest, {'allocations', 'filesystem'},
                'CONFIG QA media manifest')
        if (qa_media_manifest['filesystem'] != qa_report or
                qa_media_manifest['allocations'] != _expected_allocations(qa_payloads, spec)):
            raise AcceptanceError('CONFIG QA media inspector or allocation map drift: ' + source_row['name'])


def verify_floppy_media(run_dir, root):
    run_dir, root = Path(run_dir), Path(root)
    config = read_json(root / 'config/m17/floppy-profiles.json')
    _object(config, {'schema_version', 'd88', 'boot_record', 'profiles', 'test_file'},
            'M16 floppy profile config')
    if type(config['schema_version']) is not int or config['schema_version'] != 1:
        raise AcceptanceError('unsupported M16 floppy profile version')
    profiles = config['profiles']
    manifest = read_json(run_dir / 'floppy-media/profiles.json')
    expected_names = [item.get('name') for item in profiles if isinstance(item, dict)]
    if (len(profiles) != 5 or len(set(expected_names)) != 5 or
            set(manifest) != set(expected_names)):
        raise AcceptanceError('M16 floppy fixture set differs from the accepted formats')
    directory_files = _tree_files(run_dir / 'floppy-media')
    if directory_files != {'profiles.json'} | {name + '.d88' for name in expected_names}:
        raise AcceptanceError('M16 floppy output contains missing or unexpected files')
    for profile in profiles:
        name = profile['name']
        row = manifest[name]
        _object(row, FLOPPY_ROW_FIELDS, 'M16 floppy output record ' + name)
        spec = profile_spec(profile, config, 1787814827)
        content = profile_payload(profile, config['test_file']['content_template'])
        geometry = profile['geometry']
        capacity = (geometry['cylinders'] * geometry['heads'] *
                    geometry['sectors_per_track'] * geometry['bytes_per_sector'])
        target = _safe_file(run_dir / 'floppy-media', name + '.d88', 'M16 floppy image')
        if (row['guest_media_id'] != profile['guest_media_id'] or
                row['geometry'] != profile['geometry'] or
                row['payload_bytes'] != len(content) or
                row['raw_capacity_bytes'] != capacity or
                row['d88_size'] != target.stat().st_size or
                not isinstance(row['d88_sha256'], str) or
                not HEX64.fullmatch(row['d88_sha256']) or
                row['d88_sha256'] != _hash_file(target)):
            raise AcceptanceError('M16 floppy image record differs from source: ' + name)
        try:
            report, files = inspect_d88(target.read_bytes(), spec)
        except (OSError, ValueError, KeyError, struct.error) as error:
            raise AcceptanceError('M16 floppy D88 inspector failed: ' + name + ': ' + str(error)) from error
        if (files != {config['test_file']['dos_name']: content} or
                row['filesystem'] != report or report.get('fat_copies_equal') is not True):
            raise AcceptanceError('M16 floppy FAT readback differs from its profile: ' + name)
        if spec['filesystem'].get('fat_type') != 'FAT12':
            raise AcceptanceError('M16 floppy regression profile is not FAT12: ' + name)


def verify_storage_fixtures(run_dir, root):
    profiles = load_storage_profiles(Path(root) / 'config/m17/media-profiles.json')
    if len(profiles) != 6:
        raise AcceptanceError('M17 storage fixture profile count changed')
    result = _verify_manifest(Path(run_dir) / 'storage-media', profiles)
    if len(result) != 6:
        raise AcceptanceError('independent M17 storage inspection incomplete')
    for profile in profiles:
        if (profile['deployment']['bootable_fixture'] is not False or
                profile['qualification']['guest'] != 'NOT_QUALIFIED' or
                profile['qualification']['hardware'] != 'NOT_RUN'):
            raise AcceptanceError('storage fixture overstates runtime qualification')


def _validate_schema_in_pinned_container(inputs, root, image):
    """Validate the committed schema and instance with all six pinned wheels."""
    specs = host_wheel_specs()[1:]
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode='w') as archive:
        for spec in specs:
            archive.add(Path(inputs) / spec['filename'], arcname='wheels/' + spec['filename'])
        archive.add(Path(root) / 'config/m17/media-profiles.schema.json',
                    arcname='config/media-profiles.schema.json')
        archive.add(Path(root) / 'config/m17/media-profiles.json',
                    arcname='config/media-profiles.json')
    program = r'''import json, pathlib, shutil, sys, tarfile, zipfile
root=pathlib.Path('/tmp/m17-schema-verify')
root.mkdir()
with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as archive:
    for member in archive:
        path=pathlib.PurePosixPath(member.name)
        assert member.isfile() and not path.is_absolute() and all(part not in ('', '.', '..') for part in path.parts)
        target=root.joinpath(*path.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.extractfile(member) as source, target.open('wb') as output:
            shutil.copyfileobj(source, output)
deps=root/'deps'; deps.mkdir()
for wheel in sorted((root/'wheels').glob('*.whl')):
    with zipfile.ZipFile(wheel) as source:
        source.extractall(deps)
sys.path.insert(0, str(deps))
from jsonschema import Draft202012Validator, FormatChecker
schema=json.loads((root/'config/media-profiles.schema.json').read_text())
instance=json.loads((root/'config/media-profiles.json').read_text())
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)
print('M17_PROFILE_SCHEMA_AND_INSTANCE_VALID')
'''
    command = [
        'docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none',
        '-i', '--entrypoint', 'python3', image, '-c', program,
    ]
    result = subprocess.run(command, input=payload.getvalue(), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if result.returncode:
        detail = result.stderr.decode('utf-8', 'replace')[-4000:]
        raise AcceptanceError('pinned JSON Schema validation failed: ' + detail)
    if b'M17_PROFILE_SCHEMA_AND_INSTANCE_VALID' not in result.stdout:
        raise AcceptanceError('pinned JSON Schema validator returned no pass marker')


def verify_component_remotes(root):
    """Check actual topic remotes and run their isolated safety regressions."""
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    commands = (
        [sys.executable, '-B', str(Path(root) / 'tools/m17/component_remotes.py')],
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
         str(Path(root) / 'tests/m17'), '-p', 'test_component_remotes.py'],
    )
    for command in commands:
        result = subprocess.run(command, cwd=root, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True)
        if result.returncode:
            raise AcceptanceError('component remote validation failed: ' + result.stdout[-4000:])


def _verify_top_level(build_dir):
    expected = {
        'inputs', 'run-1', 'run-2', 'build-1.log', 'build-2.log',
        'media.d88', 'build.json',
    }
    root = Path(build_dir)
    if root.is_symlink() or not root.is_dir():
        raise AcceptanceError('build output path is missing or unsafe')
    entries = set()
    for path in root.iterdir():
        if path.is_symlink():
            raise AcceptanceError('build output contains a top-level symlink')
        entries.add(path.name)
    if entries != expected:
        raise AcceptanceError('build output has missing or unexpected top-level entries')


def verify(build_dir, root=ROOT):
    build_dir, root = Path(build_dir), Path(root).resolve()
    if build_dir.is_symlink():
        raise AcceptanceError('build output path must not be a symlink')
    build_dir = build_dir.resolve()
    try:
        build_dir.relative_to(root)
    except ValueError as error:
        raise AcceptanceError('build output must be inside the active M17 checkout') from error
    if subprocess.run(['git', '-C', str(root), 'check-ignore', '-q', str(build_dir / 'probe')]).returncode:
        raise AcceptanceError('build output is not Git-excluded')
    _verify_top_level(build_dir)

    record = read_json(build_dir / 'build.json')
    validate_build_record(record)
    verify_source_inputs(build_dir, root, record)
    verify_component_remotes(root)

    for number in (1, 2):
        run_dir = build_dir / f'run-{number}'
        artifact_path = read_json(run_dir / 'artifacts.json')
        if artifact_path != record['artifacts']:
            raise AcceptanceError(f'run-{number} manifest differs from the final build record')
        validate_artifact_tree(run_dir, artifact_path)
        verify_build_log(build_dir / f'build-{number}.log', tests_required=(number == 1))
        verify_distribution_media(run_dir, root)
        verify_floppy_media(run_dir, root)
        verify_storage_fixtures(run_dir, root)

    if (build_dir / 'run-1/artifacts.json').read_bytes() != (build_dir / 'run-2/artifacts.json').read_bytes():
        raise AcceptanceError('independent clean build manifests are not byte-identical')
    media = _safe_file(build_dir, 'media.d88', 'final build candidate').read_bytes()
    for number in (1, 2):
        if media != _safe_file(build_dir / f'run-{number}', 'media.d88', 'clean-build D88').read_bytes():
            raise AcceptanceError('top-level D88 differs from an independent clean build')
    _validate_schema_in_pinned_container(build_dir / 'inputs', root, record['toolchain_image'])
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True,
                        help='output directory created by tools/m17/build_image.py')
    args = parser.parse_args(argv)
    try:
        result = verify(args.build)
    except (AcceptanceError, ContractError, OSError, subprocess.CalledProcessError,
            KeyError, TypeError, ValueError) as error:
        print('M17 build acceptance failed: ' + str(error), file=sys.stderr)
        return 1
    print('M17 BUILD ACCEPTANCE VERIFIED')
    print('Source parent: ' + result['sources']['parent'])
    print('Two independent clean builds and artifact bytes match.')
    print('Media schema/instance, storage fixtures, CONFIG QA images, and M16 floppy regressions validated.')
    print('Guest boot: NOT RUN; hardware: NOT RUN.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
