#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed M16 evidence, source-binding, and publication verifier."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import re
import subprocess


class Rejected(ValueError):
    """A stable acceptance rejection code."""


def require(condition, code):
    if not condition:
        raise Rejected(code)


def json_value(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'DUPLICATE_JSON_FIELD')
            result[key] = value
        return result
    try:
        return json.loads(text, object_pairs_hook=unique)
    except (UnicodeError, json.JSONDecodeError):
        raise Rejected('INVALID_JSON') from None


def validate_schema(schema):
    """Validate the closed JSON Schema subset used by M16 records."""
    allowed = {'$schema', '$id', 'title', 'description', 'type', 'const', 'enum',
               'required', 'properties', 'additionalProperties', 'pattern',
               'minimum', 'maximum', 'items', 'minItems', 'maxItems'}
    types = {'object', 'array', 'string', 'integer', 'number', 'boolean', 'null'}

    def walk(node):
        require(isinstance(node, dict), 'INVALID_SCHEMA')
        require(set(node) <= allowed, 'UNSUPPORTED_SCHEMA_KEYWORD')
        if '$schema' in node:
            require(node['$schema'] == 'https://json-schema.org/draft/2020-12/schema',
                    'INVALID_SCHEMA')
        if '$id' in node:
            require(isinstance(node['$id'], str) and node['$id'], 'INVALID_SCHEMA')
        if 'type' in node:
            require(node['type'] in types, 'INVALID_SCHEMA')
        if 'required' in node:
            value = node['required']
            require(isinstance(value, list) and all(isinstance(x, str) and x for x in value)
                    and len(set(value)) == len(value), 'INVALID_SCHEMA')
        if 'properties' in node:
            props = node['properties']
            require(isinstance(props, dict) and all(isinstance(k, str) for k in props),
                    'INVALID_SCHEMA')
            for child in props.values():
                walk(child)
        if 'additionalProperties' in node:
            extra = node['additionalProperties']
            require(type(extra) is bool or isinstance(extra, dict), 'INVALID_SCHEMA')
            if isinstance(extra, dict):
                walk(extra)
        if 'items' in node:
            walk(node['items'])
        if 'pattern' in node:
            require(isinstance(node['pattern'], str), 'INVALID_SCHEMA')
            try:
                re.compile(node['pattern'])
            except re.error:
                raise Rejected('INVALID_SCHEMA') from None
        for key in ('minimum', 'maximum', 'minItems', 'maxItems'):
            if key in node:
                require(type(node[key]) in (int, float) and node[key] >= 0,
                        'INVALID_SCHEMA')
        if 'enum' in node:
            require(isinstance(node['enum'], list) and node['enum'], 'INVALID_SCHEMA')
    walk(schema)


def validate_instance(schema, value):
    """Validate a JSON instance using the M16 schema's supported keywords."""
    def walk(spec, item):
        kind = spec.get('type')
        if kind == 'object':
            require(isinstance(item, dict), 'INVALID_INSTANCE')
            for key in spec.get('required', []):
                require(key in item, 'INVALID_INSTANCE')
            properties = spec.get('properties', {})
            extra = spec.get('additionalProperties', True)
            for key, child in item.items():
                if key in properties:
                    walk(properties[key], child)
                elif extra is False:
                    raise Rejected('INVALID_INSTANCE')
                elif isinstance(extra, dict):
                    walk(extra, child)
        elif kind == 'array':
            require(isinstance(item, list), 'INVALID_INSTANCE')
            if 'minItems' in spec:
                require(len(item) >= spec['minItems'], 'INVALID_INSTANCE')
            if 'maxItems' in spec:
                require(len(item) <= spec['maxItems'], 'INVALID_INSTANCE')
            if 'items' in spec:
                for child in item:
                    walk(spec['items'], child)
        elif kind == 'string':
            require(isinstance(item, str), 'INVALID_INSTANCE')
            if 'pattern' in spec:
                require(re.search(spec['pattern'], item) is not None, 'INVALID_INSTANCE')
        elif kind == 'integer':
            require(type(item) is int, 'INVALID_INSTANCE')
            if 'minimum' in spec:
                require(item >= spec['minimum'], 'INVALID_INSTANCE')
            if 'maximum' in spec:
                require(item <= spec['maximum'], 'INVALID_INSTANCE')
        elif kind == 'number':
            require(type(item) in (int, float), 'INVALID_INSTANCE')
            if 'minimum' in spec:
                require(item >= spec['minimum'], 'INVALID_INSTANCE')
            if 'maximum' in spec:
                require(item <= spec['maximum'], 'INVALID_INSTANCE')
        elif kind == 'boolean':
            require(type(item) is bool, 'INVALID_INSTANCE')
        elif kind == 'null':
            require(item is None, 'INVALID_INSTANCE')
        if 'const' in spec:
            require(item == spec['const'] and type(item) is type(spec['const']),
                    'INVALID_INSTANCE')
        if 'enum' in spec:
            require(any(item == choice and type(item) is type(choice)
                        for choice in spec['enum']), 'INVALID_INSTANCE')
    walk(schema, value)


def safe_file(root, relative):
    require(isinstance(relative, str) and relative, 'INVALID_ARTIFACT_PATH')
    path = PurePosixPath(relative)
    require(not path.is_absolute() and all(part not in ('', '.', '..') for part in path.parts),
            'INVALID_ARTIFACT_PATH')
    target = root.joinpath(*path.parts)
    current = root
    for part in path.parts:
        current = current / part
        require(not current.is_symlink(), 'SYMLINK_ARTIFACT')
    require(target.is_file(), 'MISSING_ARTIFACT')
    return target


def bound_file(root, relative, expected_size=None, expected_sha=None,
               size_code='ARTIFACT_SIZE_DRIFT', digest_code='ARTIFACT_DIGEST_DRIFT'):
    data = safe_file(root, relative).read_bytes()
    if expected_size is not None:
        require(type(expected_size) is int and len(data) == expected_size, size_code)
    if expected_sha is not None:
        check_digest(expected_sha)
        require(sha256(data) == expected_sha, digest_code)
    return data


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def check_commit(value):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}', value) is not None,
            'INVALID_COMMIT_ID')
    require(value != '0' * 40, 'INVALID_COMMIT_ID')


def check_digest(value):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
            'INVALID_DIGEST')
    require(value != '0' * 64, 'INVALID_DIGEST')


def verify_ancestry(root, start, qualified, publication=None):
    for value in (start, qualified) + ((publication,) if publication else ()):
        check_commit(value)
    pair = (start, qualified) if publication is None else (start, qualified, publication)
    require(len(set(pair)) == len(pair), 'IDENTITY_COLLISION')
    edges = [(start, qualified)]
    if publication is not None:
        edges.append((qualified, publication))
    for ancestor, descendant in edges:
        require(subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor',
                                ancestor, descendant], stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL).returncode == 0, 'ANCESTRY_MISMATCH')


def verify_distinct_commits(values):
    commits = list(values.values()) if isinstance(values, dict) else list(values)
    for value in commits:
        check_commit(value)
    require(len(set(commits)) == len(commits), 'IDENTITY_COLLISION')


def verify_required_ci_heads(claims, required_heads):
    claimed = {claim.get('head_sha') for claim in claims if isinstance(claim, dict)}
    require(set(required_heads) <= claimed, 'REQUIRED_SOURCE_CI_MISSING')


def verify_candidate(root):
    schema = json_value((root / 'config/m16/acceptance.schema.json').read_text())
    record = json_value((root / 'config/m16/acceptance.json').read_text())
    validate_schema(schema)
    validate_instance(schema, record)
    validate_schema(json_value((root / 'config/m16/publication.schema.json').read_text()))

    identities = record['identities']
    verify_distinct_commits(identities)
    check_commit(git(root, 'rev-parse', 'HEAD'))
    verify_ancestry(root, identities['START_SHA'], identities['QUALIFIED_IMPLEMENTATION_SHA'])
    require(subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor',
                            identities['QUALIFIED_IMPLEMENTATION_SHA'], 'HEAD'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
            'QUALIFIED_SOURCE_NOT_ANCESTOR')
    for value in identities.values():
        require(subprocess.run(['git', '-C', str(root), 'cat-file', '-e', value + '^{commit}'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
                'UNREACHABLE_IDENTITY')

    for name, path in (('fdkernel', 'components/fdkernel'),
                       ('freecom', 'components/freecom'), ('country', 'components/country')):
        expected = record['components'][name]
        check_commit(expected)
        tree = git(root, 'ls-tree', 'HEAD', '--', path).split()
        require(tree[:3] == ['160000', 'commit', expected], 'COMPONENT_GITLINK_DRIFT')
        require(git(root / path, 'rev-parse', 'HEAD') == expected, 'COMPONENT_HEAD_DRIFT')
        require(not git(root / path, 'status', '--porcelain', '--untracked-files=all'),
                'DIRTY_COMPONENT')

    report_ref = record['report']
    report_bytes = bound_file(root, report_ref['path'], expected_sha=report_ref['sha256'],
                              digest_code='REPORT_DIGEST_DRIFT')
    report_path = root / report_ref['path']
    report_text = report_bytes.decode('utf-8')
    require('/home/' not in report_text and '.private-evidence' not in report_text,
            'PRIVATE_PATH_IN_PUBLIC_REPORT')

    distribution = record['distribution']
    manifest_bytes = bound_file(root, distribution['manifest_path'],
                                expected_sha=distribution['manifest_sha256'],
                                digest_code='MANIFEST_DIGEST_DRIFT')
    manifest_path = root / distribution['manifest_path']
    manifest = json_value(manifest_bytes.decode('utf-8'))
    distribution_schema = json_value((root / 'config/m16/distribution.schema.json').read_text())
    validate_schema(distribution_schema)
    validate_instance(distribution_schema, manifest)
    archive_bytes = bound_file(root, distribution['archive_path'],
                               expected_size=distribution['archive_bytes'],
                               expected_sha=distribution['archive_sha256'],
                               size_code='ARCHIVE_SIZE_DRIFT', digest_code='ARCHIVE_DIGEST_DRIFT')
    try:
        image_bytes = lzma.decompress(archive_bytes)
    except lzma.LZMAError:
        raise Rejected('INVALID_XZ_ARCHIVE') from None
    require(len(image_bytes) == distribution['image_bytes'], 'IMAGE_SIZE_DRIFT')
    require(sha256(image_bytes) == distribution['image_sha256'], 'IMAGE_DIGEST_DRIFT')
    artifact = manifest.get('artifact', {})
    require(artifact.get('compressed', {}).get('bytes') == len(archive_bytes) and
            artifact.get('compressed', {}).get('sha256') == sha256(archive_bytes) and
            artifact.get('uncompressed', {}).get('bytes') == len(image_bytes) and
            artifact.get('uncompressed', {}).get('sha256') == sha256(image_bytes),
            'MANIFEST_ARTIFACT_DRIFT')
    source = manifest.get('rebuild_source', {})
    require(source.get('qualified_implementation') == identities['QUALIFIED_IMPLEMENTATION_SHA'],
            'QUALIFIED_SOURCE_DRIFT')
    check_commit(source.get('parent'))
    require(subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor',
                            source['parent'], 'HEAD'], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL).returncode == 0,
            'REBUILD_SOURCE_NOT_ANCESTOR')
    for name, key in (('fdkernel', 'fdkernel'), ('freecom', 'freecom'), ('country', 'country')):
        require(source.get(key) == record['components'][name], 'MANIFEST_COMPONENT_DRIFT')
    source_archives = manifest.get('source_archives_sha256', {})
    require(set(source_archives) == {'parent', 'fdkernel', 'freecom', 'country'},
            'SOURCE_ARCHIVE_BINDING_MISSING')
    for digest in source_archives.values():
        check_digest(digest)
    archive_inputs = ('tools/m16', 'tests/m16', 'config/m16',
                      'manifests/components.lock.json', 'manifests/m16-components.lock.json',
                      'manifests/toolchains.lock.json', 'COPYING', 'LICENSE.md')
    for name in ('parent', 'fdkernel', 'freecom', 'country'):
        repo = root if name == 'parent' else root / 'components' / name
        source_commit = source['parent'] if name == 'parent' else source[name]
        command = ['git', '-C', str(repo), 'archive', source_commit]
        if name == 'parent':
            command.extend(archive_inputs)
        archive_hash = sha256(subprocess.check_output(command))
        require(archive_hash == source_archives[name], 'SOURCE_ARCHIVE_DIGEST_DRIFT')
        if name != 'parent':
            tree = git(root, 'ls-tree', source['parent'], '--', 'components/' + name).split()
            require(tree[:3] == ['160000', 'commit', source_commit],
                    'REBUILD_COMPONENT_GITLINK_DRIFT')
    toolchain = manifest.get('toolchain', {})
    require(toolchain.get('linux_amd64_image') ==
            'sha256:' + record['toolchain']['linux_amd64_image_sha256'] and
            toolchain.get('unicorn_version') == record['toolchain']['unicorn_version'] and
            toolchain.get('unicorn_wheel_sha256') == record['toolchain']['unicorn_wheel_sha256'],
            'TOOLCHAIN_BINDING_DRIFT')
    profile = artifact.get('profile', {})
    require(profile.get('media') == '2HD' and profile.get('payload_capacity_bytes') == 1280 * 1024 and
            profile.get('bytes_per_sector') == 1024 and profile.get('role') == 'bootable distribution',
            'PROFILE_BINDING_DRIFT')

    vaeg = json_value((root / 'config/m16/vaeg-candidate.json').read_text())
    check_commit(record['vaeg']['commit'])
    require(vaeg.get('source', {}).get('commit') == record['vaeg']['commit'] and
            vaeg.get('builds', {}).get('linux', {}).get('executable_sha256') ==
            record['vaeg']['linux_executable_sha256'] and
            vaeg.get('builds', {}).get('windows_mingw64', {}).get('executable_sha256') ==
            record['vaeg']['mingw64_executable_sha256'] and
            vaeg.get('builds', {}).get('windows_mingw64', {}).get('workflow_run_id') ==
            record['vaeg']['ci_run_id'], 'VAEG_BINDING_DRIFT')

    forbidden = {'/home/', '.private-evidence', 'PC88VA.ROM', 'PC88VA2.ROM'}
    for path in (root / 'config/m16/acceptance.json', report_path, manifest_path,
                 root / 'images/milestones/m16/README.md'):
        text = path.read_text(errors='replace')
        require(not any(token in text for token in forbidden), 'PRIVATE_DATA_IN_PUBLIC_INPUTS')
    allowed = {distribution['archive_path'], distribution['manifest_path'],
               'images/milestones/m16/README.md'}
    files = {path.name for path in (root / 'images/milestones/m16').iterdir() if path.is_file()}
    require(files == {PurePosixPath(x).name for x in allowed}, 'UNEXPECTED_MILESTONE_ARTIFACT')
    return record


def verify_ci_claim(claim, run, jobs):
    required = {'repository', 'run_id', 'attempt', 'head_sha', 'workflow_path', 'required_jobs'}
    require(isinstance(claim, dict) and set(claim) == required, 'INVALID_CI_CLAIM')
    check_commit(claim['head_sha'])
    require(run.get('repository', {}).get('full_name') == claim['repository'],
            'CI_REPOSITORY_DRIFT')
    require(run.get('id') == claim['run_id'] and run.get('run_attempt') == claim['attempt'],
            'CI_ATTEMPT_DRIFT')
    require(run.get('head_sha') == claim['head_sha'], 'CI_HEAD_SHA_DRIFT')
    require(run.get('path') == claim['workflow_path'], 'CI_WORKFLOW_DRIFT')
    require(run.get('status') == 'completed' and run.get('conclusion') == 'success',
            'CI_NOT_SUCCESS')
    require(isinstance(claim['required_jobs'], list) and claim['required_jobs'],
            'CI_REQUIRED_JOBS_MISSING')
    for name in claim['required_jobs']:
        matches = [job for job in jobs if job.get('name') == name]
        require(len(matches) == 1 and matches[0].get('conclusion') == 'success' and
                matches[0].get('head_sha') == claim['head_sha'], 'CI_JOB_NOT_QUALIFIED')


def gh_json(*args):
    return json.loads(subprocess.check_output(['gh', 'api', *args], text=True))


def verify_publication(root, record_path):
    record = json_value(record_path.read_text())
    schema = json_value((root / 'config/m16/publication.schema.json').read_text())
    validate_schema(schema)
    validate_instance(schema, record)
    identities = record['identities']
    expected_ids = {'START_SHA', 'QUALIFIED_IMPLEMENTATION_SHA',
                    'PUBLICATION_TIP_SHA', 'DOWNSTREAM_BASE_SHA'}
    require(isinstance(identities, dict) and set(identities) == expected_ids,
            'INVALID_PUBLICATION_IDENTITIES')
    verify_distinct_commits(identities)
    tip = identities['PUBLICATION_TIP_SHA']
    verify_ancestry(root, identities['START_SHA'], identities['QUALIFIED_IMPLEMENTATION_SHA'], tip)
    require(record['repository'] == 'nakatamaho/freedos-pc88va' and
            record['remote'] == 'origin' and
            record['branch'] == 'topic/m16-floppy-formats-console-input',
            'PUBLICATION_TARGET_DRIFT')
    require(git(root, 'rev-parse', 'HEAD') == tip, 'PUBLICATION_CHECKOUT_DRIFT')
    require(git(root, 'branch', '--show-current') == record['branch'],
            'PUBLICATION_BRANCH_DRIFT')
    remote = git(root, 'ls-remote', '--heads', record['remote'],
                 'refs/heads/' + record['branch']).split()
    require(len(remote) == 2 and remote[0] == tip and
            remote[1] == 'refs/heads/' + record['branch'], 'REMOTE_TIP_MISMATCH')
    for value in identities.values():
        require(subprocess.run(['git', '-C', str(root), 'cat-file', '-e', value + '^{commit}'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
                'UNREACHABLE_IDENTITY')
    allowed = {
        '.github/workflows/m16-source-build.yml',
        'config/m16/acceptance.json', 'config/m16/acceptance.schema.json',
        'config/m16/publication.schema.json', 'config/m16/distribution.schema.json',
        'docs/porting/m16-report.md',
        'images/milestones/m16/README.md', 'images/milestones/m16/manifest.json',
        'images/milestones/m16/freedos-pc88va-m16-2hd-1280.d88.xz',
        'tests/m16/test_acceptance.py', 'tools/m16/verify_acceptance.py',
        'tools/m16/build_image.sh', 'tools/m16/README.md'
    }
    changes = set(git(root, 'diff', '--name-only', identities['QUALIFIED_IMPLEMENTATION_SHA'],
                      tip).splitlines())
    require(changes and changes <= allowed, 'UNAPPROVED_PUBLICATION_DIFF')
    claims = record['ci']
    require(isinstance(claims, list) and claims, 'CI_EVIDENCE_MISSING')
    candidate_record = json_value((root / 'config/m16/acceptance.json').read_text())
    required_heads = {tip, candidate_record['components']['fdkernel'],
                      candidate_record['vaeg']['commit']}
    verify_required_ci_heads(claims, required_heads)
    for claim in claims:
        repository = claim.get('repository')
        run_id = claim.get('run_id')
        attempt = claim.get('attempt')
        require(isinstance(repository, str) and isinstance(run_id, int) and isinstance(attempt, int),
                'INVALID_CI_CLAIM')
        endpoint = f"repos/{repository}/actions/runs/{run_id}"
        run = gh_json(endpoint)
        pages = gh_json('--paginate', '--slurp',
                        endpoint + f'/attempts/{attempt}/jobs?per_page=100')
        jobs = [job for page in pages for job in page.get('jobs', [])]
        verify_ci_claim(claim, run, jobs)
    candidate = verify_candidate(root)
    for key in ('START_SHA', 'QUALIFIED_IMPLEMENTATION_SHA', 'DOWNSTREAM_BASE_SHA'):
        require(candidate['identities'][key] == identities[key], 'CANDIDATE_BINDING_DRIFT')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--mode', choices=('candidate', 'publication'), default='candidate')
    parser.add_argument('--publication-record', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.mode == 'candidate':
            require(args.publication_record is None, 'UNEXPECTED_PUBLICATION_RECORD')
            verify_candidate(root)
            print('M16 candidate record, schema, provenance, archive, and privacy checks passed')
        else:
            require(args.publication_record is not None, 'PUBLICATION_RECORD_REQUIRED')
            verify_publication(root, args.publication_record.resolve())
            print('M16 publication topology, exact-tip CI, and bounded-diff checks passed')
    except (Rejected, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError,
            lzma.LZMAError) as error:
        print(str(error) if isinstance(error, Rejected) else 'M16_ACCEPTANCE_GATE_ERROR')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
