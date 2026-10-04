# SPDX-License-Identifier: GPL-2.0-or-later
"""Negative instance tests for the M20-local distribution acceptance gate."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/m20'))
from verify_distribution import (BUILD_FIELDS, COMPONENTS, VerificationError,
                                 bound_file, check_manifest, check_utility, fields, verify)
from compose_image import compose_data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def instances():
    parent, start = 'a' * 40, 'c' * 40
    revisions = {'parent': parent, **{n: 'b' * 40 for n in COMPONENTS}}
    payloads = {n: n.encode() for n in revisions}
    archives = {n: sha(payloads[n]) for n in revisions}
    source = {'archive_members': [n + '.tar' for n in revisions],
              'parent_revision': parent, 'toolchain_identity': 'sha256:' + sha(b'lock'),
              'source_archives_sha256': archives,
              'components': {n: {'commit': revisions[n], 'source_archive_sha256': archives[n]}
                             for n in COMPONENTS}}
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:xz') as bundle:
        for name, data in {'README.txt': b'sources', 'SOURCE-MANIFEST.json':
                           json.dumps(source).encode(),
                           **{n + '.tar': data for n, data in payloads.items()}}.items():
            item = tarfile.TarInfo('pc88va-freedos-m20-source/' + name)
            item.size = len(data)
            bundle.addfile(item, io.BytesIO(data))
    manifest = dict.fromkeys(BUILD_FIELDS)
    manifest.update(schema_version=1, milestone='M20', hardware='NOT RUN',
                    guest_boot='NOT RUN BY make m20-disk', parent_revision=parent,
                    parent_start_sha=start, component_revisions=revisions,
                    source_archives_sha256=archives, two_independent_clean_builds_equal=True,
                    toolchain_identity='sha256:' + sha(b'lock'),
                    distribution_d88={'sha256': 'e' * 64, 'size_bytes': 100},
                    utility_d88={'sha256': 'd' * 64, 'size_bytes': 100},
                    utility_manifest_sha256='d' * 64)
    comparison = dict(schema_version=1, independent_clean_builds=2,
                      media_d88_byte_identical=True,
                      release_capacity_records_identical=True,
                      release_package_records_identical=True,
                      media_d88_sha256='e' * 64,
                      utility_d88_byte_identical=True,
                      release_utility_records_identical=True,
                      utility_d88_sha256='d' * 64,
                      diagnostic_maps_are_not_part_of_the_distribution_reproducibility_claim=True)
    files = {'TEST.TXT': b'hello', 'CONFIG.SYS': b'config'}
    budget = dict(schema_version=1, profile_id='synthetic', geometry={},
                  d88_and_fat_readback='PASS',
                  container={'sha256': 'e' * 64,
                             'size_bytes': 100, 'format': 'D88'},
                  filesystem={'file_records': {
                      n: {'sha256': sha(data), 'size_bytes': len(data)}
                      for n, data in files.items()}},
                  workspace_budget={'sample_workflow_cluster_budget': 32,
                                    'configured_free_clusters_floor': 128,
                                    'guest_peak_measurement': 'NOT MEASURED'})
    packages = dict(schema_version=1, milestone='M20', parent_revision=parent,
                    parent_start_sha=start, toolchain_identity=manifest['toolchain_identity'],
                    toolchain_lock_sha256=sha(b'lock'), packages=[
                        {'id': name, 'files': ['TEST.TXT'] if name == 'starter-material' else [],
                         'built_files': {'TEST.TXT': {'sha256': sha(b'hello'),
                                                     'size_bytes': 5}}
                         if name == 'starter-material' else {}, 'license': 'GPL-2.0-or-later'}
                        for name in ('fdkernel', 'freecom', 'country', 'edlin', 'more',
                                     'maintenance', 'memmap', 'jwasm', 'starter-material')])
    lock = {'start_sha': start, 'components': [
        {'name': n, 'commit': revisions[n], 'source_archive_sha256': archives[n]}
        for n in COMPONENTS]}
    return manifest, comparison, budget, packages, files, stream.getvalue(), lock, sha(b'lock')


class DistributionInstanceTests(unittest.TestCase):
    def verify(self, values):
        check_manifest(*values)

    def test_synthetic_closed_instance(self):
        self.verify(instances())

    def test_schema_unknown_missing_and_malformed_hash(self):
        baseline = instances()
        for modify in (lambda a: a.pop('hardware'),
                       lambda a: a.update(unknown=True),
                       lambda a: a['source_archives_sha256'].update(parent='short')):
            values = copy.deepcopy(baseline)
            modify(values[0])
            with self.subTest(modify=modify), self.assertRaises(VerificationError):
                self.verify(values)

    def test_dependency_topology_digest_and_stale_comparison(self):
        baseline = instances()
        for index, change in ((0, lambda a: a['component_revisions'].pop('edlin')),
                              (2, lambda a: a['filesystem']['file_records']['TEST.TXT']
                               .update(sha256='f' * 64)),
                              (1, lambda a: a.update(media_d88_sha256='f' * 64)),
                              (1, lambda a: a.update(utility_d88_sha256='f' * 64)),
                              (1, lambda a: a.pop('utility_d88_byte_identical')),
                              (3, lambda a: a.update(parent_revision='f' * 40)),
                              (3, lambda a: a.update(toolchain_identity='sha256:' + 'f' * 64))):
            values = copy.deepcopy(baseline)
            change(values[index])
            with self.subTest(index=index), self.assertRaises(VerificationError):
                self.verify(values)

    def test_public_filename_contract_accepts_prefix_and_rejects_old_names(self):
        manifest, comparison, budget, packages, files, bundle, lock, lock_hash = instances()
        image = b'synthetic D88'
        manifest['distribution_d88'] = {
            'filename': 'freedos-PC88VA-M20-2HD.D88',
            'sha256': sha(image), 'size_bytes': len(image)}
        manifest['source_bundle'] = {
            'filename': 'freedos-PC88VA-M20-SOURCES.tar.xz',
            'sha256': sha(bundle), 'size_bytes': len(bundle)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist = root / 'dist/m20'
            dist.mkdir(parents=True)
            (root / 'config/m20').mkdir(parents=True)
            (root / 'manifests').mkdir()
            (root / 'config/m20/media.json').write_text(json.dumps({'geometry': {}}))
            (root / 'manifests/m20-components.lock.json').write_text(json.dumps(lock))
            (root / 'manifests/toolchains.lock.json').write_bytes(b'lock')
            for key, filename, record in (
                    ('two_build_comparison_sha256', 'two-build-comparison.json', comparison),
                    ('capacity_budget_sha256', 'capacity-budget.json', budget),
                    ('package_manifest_sha256', 'package-manifest.json', packages)):
                data = json.dumps(record).encode()
                (dist / filename).write_bytes(data)
                manifest[key] = sha(data)
            (dist / manifest['distribution_d88']['filename']).write_bytes(image)
            (dist / manifest['source_bundle']['filename']).write_bytes(bundle)
            with patch('verify_distribution.inspect', return_value=(
                    {'fat_copies_equal': True}, files)), patch(
                    'verify_distribution.check_manifest') as check, patch(
                    'verify_distribution.check_utility'):
                (dist / 'build-manifest.json').write_text(json.dumps(manifest))
                verify(root, dist)
                check.assert_called_once()
                for key, name in (
                        ('distribution_d88', 'PC88VA-M20-2HD.D88'),
                        ('source_bundle', 'PC88VA-M20-SOURCES.tar.xz')):
                    old = copy.deepcopy(manifest)
                    old[key]['filename'] = name
                    (dist / 'build-manifest.json').write_text(json.dumps(old))
                    with self.subTest(key=key), self.assertRaisesRegex(
                            VerificationError, 'filename differs'):
                        verify(root, dist)

    def test_utility_disk_instance_and_negatives(self):
        root_source = Path(__file__).resolve().parents[2]
        config = {'schema_version': 1, 'milestone': 'M20',
                  'disk': {'filename': 'freedos-PC88VA-M20-UTIL.D88', 'd88_disk_name': 'FDOS-PC88VA-UTIL',
                           'volume_label': 'M20-UTIL', 'role': 'data'},
                  'readme': 'config/m20/utility/README.TXT',
                  'notices': {'COPYING': 'COPYING'},
                  'packages': [{'id': 'find', 'files': ['FIND.EXE'], 'source_locks': ['find'],
                                'license': 'GPL', 'builder': 'utilities.build_find'}]}
        payloads = {'FIND.EXE': b'MZ' + bytes(100), 'COPYING': b'gpl\r\n', 'README.TXT': b'r\r\n'}
        lock = {'start_sha': 'c' * 40, 'components': [
            {'name': 'find', 'commit': '1' * 40, 'source_archive_sha256': '2' * 64}]}

        def build(mutate=None):
            tmp = tempfile.mkdtemp()
            root = Path(tmp)
            (root / 'config/m20').mkdir(parents=True)
            (root / 'config/m20/media.json').write_bytes((root_source / 'config/m20/media.json').read_bytes())
            dist = root / 'dist'
            dist.mkdir()
            image = compose_data(payloads, dist, 1791023315, 'FDOS-PC88VA-UTIL', 'M20-UTIL')
            (dist / config['disk']['filename']).write_bytes(image)
            utility = {'schema_version': 1, 'milestone': 'M20', 'parent_revision': 'a' * 40,
                       'toolchain_identity': 'sha256:' + 'b' * 64,
                       'guest_qualification': 'NOT RUN BY make m20-disk',
                       'disk': dict(config['disk'], sha256=sha(image), size_bytes=len(image)),
                       'files': {n: {'sha256': sha(d), 'size_bytes': len(d)} for n, d in payloads.items()},
                       'notices': {'COPYING': {}},
                       'packages': [{'id': 'find', 'files': ['FIND.EXE'], 'license': 'GPL',
                                     'built_files': {'FIND.EXE': {'sha256': sha(payloads['FIND.EXE'])}},
                                     'source_identity': {'find': {'commit': '1' * 40,
                                                                  'source_archive_sha256': '2' * 64}}}]}
            cfg = copy.deepcopy(config)
            if mutate:
                mutate(utility, cfg)
            (root / 'config/m20/utility-disk.json').write_text(json.dumps(cfg))
            data = json.dumps(utility).encode()
            (dist / 'utility-manifest.json').write_bytes(data)
            manifest = {'parent_revision': 'a' * 40, 'toolchain_identity': 'sha256:' + 'b' * 64,
                        'utility_d88': {'filename': cfg['disk']['filename'], 'sha256': sha(image),
                                        'size_bytes': len(image)},
                        'utility_manifest_sha256': sha(data)}
            return root, dist, manifest

        root, dist, manifest = build()
        check_utility(root, dist, manifest, lock)
        for mutate in (
                lambda u, c: u['files']['FIND.EXE'].update(sha256='f' * 64),
                lambda u, c: u['packages'][0]['source_identity']['find'].update(commit='9' * 40),
                lambda u, c: u.update(packages=[]),
                lambda u, c: u.update(parent_revision='f' * 40),
                lambda u, c: c['notices'].update({'EXTRA.TXT': 'COPYING'}),
                lambda u, c: u.update(unknown=True)):
            root, dist, manifest = build(mutate)
            with self.subTest(mutate=mutate), self.assertRaises((VerificationError, KeyError)):
                check_utility(root, dist, manifest, lock)

    def test_source_bundle_missing_archive_member(self):
        values = list(instances())
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w:xz') as bundle:
            entry = tarfile.TarInfo('pc88va-freedos-m20-source/README.txt')
            entry.size = 1
            bundle.addfile(entry, io.BytesIO(b'x'))
        values[5] = raw.getvalue()
        with self.assertRaises(VerificationError):
            self.verify(values)

    def test_bound_file_rejects_drift_unsafe_names_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'test').write_bytes(b'abc')
            self.assertEqual(bound_file(path, 'test', sha(b'abc'), 3), b'abc')
            for name, expected in (('../test', sha(b'abc')),
                                   ('test', sha(b'def')),
                                   ('test', 'invalid'),
                                   ('missing', sha(b'abc'))):
                with self.subTest(name=name, expected=expected), self.assertRaises(
                        (VerificationError, FileNotFoundError)):
                    bound_file(path, name, expected, 3)


if __name__ == '__main__':
    unittest.main()
