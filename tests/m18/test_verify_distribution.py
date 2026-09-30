# SPDX-License-Identifier: GPL-2.0-or-later
"""Negative instance tests for the M18-local distribution acceptance gate."""
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/m18'))
from verify_distribution import (BUILD_FIELDS, COMPONENTS, VerificationError,
                                 bound_file, check_manifest, fields, verify)


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
            item = tarfile.TarInfo('pc88va-freedos-m18-source/' + name)
            item.size = len(data)
            bundle.addfile(item, io.BytesIO(data))
    manifest = dict.fromkeys(BUILD_FIELDS)
    manifest.update(schema_version=1, milestone='M18', hardware='NOT RUN',
                    guest_boot='NOT RUN BY make m18-disk', parent_revision=parent,
                    parent_start_sha=start, component_revisions=revisions,
                    source_archives_sha256=archives, two_independent_clean_builds_equal=True,
                    toolchain_identity='sha256:' + sha(b'lock'),
                    distribution_d88={'sha256': 'e' * 64, 'size_bytes': 100})
    comparison = dict(schema_version=1, independent_clean_builds=2,
                      media_d88_byte_identical=True,
                      release_capacity_records_identical=True,
                      release_package_records_identical=True,
                      media_d88_sha256='e' * 64,
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
    packages = dict(schema_version=1, milestone='M18', parent_revision=parent,
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
            'filename': 'freedos-PC88VA-M18-2HD.D88',
            'sha256': sha(image), 'size_bytes': len(image)}
        manifest['source_bundle'] = {
            'filename': 'freedos-PC88VA-M18-SOURCES.tar.xz',
            'sha256': sha(bundle), 'size_bytes': len(bundle)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist = root / 'dist/m18'
            dist.mkdir(parents=True)
            (root / 'config/m18').mkdir(parents=True)
            (root / 'manifests').mkdir()
            (root / 'config/m18/media.json').write_text(json.dumps({'geometry': {}}))
            (root / 'manifests/m18-components.lock.json').write_text(json.dumps(lock))
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
                    'verify_distribution.check_manifest') as check:
                (dist / 'build-manifest.json').write_text(json.dumps(manifest))
                verify(root, dist)
                check.assert_called_once()
                for key, name in (
                        ('distribution_d88', 'PC88VA-M18-2HD.D88'),
                        ('source_bundle', 'PC88VA-M18-SOURCES.tar.xz')):
                    old = copy.deepcopy(manifest)
                    old[key]['filename'] = name
                    (dist / 'build-manifest.json').write_text(json.dumps(old))
                    with self.subTest(key=key), self.assertRaisesRegex(
                            VerificationError, 'filename differs'):
                        verify(root, dist)

    def test_source_bundle_missing_archive_member(self):
        values = list(instances())
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w:xz') as bundle:
            entry = tarfile.TarInfo('pc88va-freedos-m18-source/README.txt')
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
