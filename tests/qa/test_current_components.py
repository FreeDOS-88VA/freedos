# SPDX-License-Identifier: GPL-2.0-or-later
"""Regression tests for explicit, schema-bound current component selection."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/qa'))
import current_components


class CurrentComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.lock = current_components._load_json(ROOT / current_components.M17_LOCK)

    def test_selector_names_and_hash_binds_the_current_lock(self):
        lock_path, milestone = current_components._select_current_lock(ROOT)
        self.assertEqual(lock_path, current_components.M20_LOCK)
        self.assertEqual(milestone, 'M20')
        selector = current_components._load_canonical_json(ROOT / current_components.CURRENT_SOURCE)
        self.assertEqual(selector['source']['sha256'],
                         hashlib.sha256((ROOT / lock_path).read_bytes()).hexdigest())

    def test_provenance_schema_normalizes_to_exact_component_gitlinks(self):
        normalized = current_components._normalize_m17_lock(self.lock)
        self.assertEqual(normalized['status'], 'current-m17')
        self.assertEqual(normalized['milestone'], 'M17')
        by_path = {item['path']: item['commit'] for item in normalized['components']}
        self.assertEqual(by_path, {
            'components/country': '23f189cca3420606eae8723884fa92ccd65eb307',
            'components/fdkernel': 'e87e8071c355a99a7f34a8758d4a3368b6523f3d',
            'components/freecom': '29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e',
        })

    def test_m17_provenance_rejects_wrong_type_status_and_component_binding(self):
        mutations = []
        wrong_schema = copy.deepcopy(self.lock)
        wrong_schema['schema_version'] = 1
        mutations.append(wrong_schema)
        wrong_milestone = copy.deepcopy(self.lock)
        wrong_milestone['milestone'] = 'M16'
        mutations.append(wrong_milestone)
        stale_status = copy.deepcopy(self.lock)
        stale_status['status'] = 'M17 implementation and qualification pending'
        mutations.append(stale_status)
        unknown_field = copy.deepcopy(self.lock)
        unknown_field['extra'] = True
        mutations.append(unknown_field)
        malformed_commit = copy.deepcopy(self.lock)
        malformed_commit['components'][0]['commit'] = 'bad'
        mutations.append(malformed_commit)
        drifted_merge = copy.deepcopy(self.lock)
        drifted_merge['components'][1]['merge_parents'][0] = '0' * 40
        mutations.append(drifted_merge)
        duplicate_component = copy.deepcopy(self.lock)
        duplicate_component['components'][2] = copy.deepcopy(duplicate_component['components'][0])
        mutations.append(duplicate_component)
        for lock in mutations:
            with self.subTest(lock=lock), self.assertRaises(current_components.CurrentComponentError):
                current_components._normalize_m17_lock(lock)

    def test_m17_provenance_cannot_be_selected_without_its_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / 'manifests'
            manifests.mkdir()
            (manifests / 'm17-components.lock.json').write_text('{}\n')
            with self.assertRaisesRegex(current_components.CurrentComponentError,
                                        'explicit current-component selector'):
                current_components._select_current_lock(root)

    def test_selector_rejects_schema_path_and_digest_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / 'manifests'
            manifests.mkdir()
            lock_bytes = b'{"milestone":"M17"}\n'
            (manifests / 'm17-components.lock.json').write_bytes(lock_bytes)
            selector = {
                'kind': 'current-component-source',
                'milestone': 'M17',
                'schema_version': 1,
                'source': {
                    'path': 'manifests/m17-components.lock.json',
                    'schema_version': 2,
                    'sha256': hashlib.sha256(lock_bytes).hexdigest(),
                },
            }

            def write_selector(value):
                data = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
                (manifests / 'current-components.json').write_bytes(data)

            write_selector(selector)
            self.assertEqual(current_components._select_current_lock(root),
                             (current_components.M17_LOCK, 'M17'))
            for mutation in ('schema', 'path', 'digest', 'unknown'):
                bad = copy.deepcopy(selector)
                if mutation == 'schema':
                    bad['source']['schema_version'] = 1
                elif mutation == 'path':
                    bad['source']['path'] = '../outside.json'
                elif mutation == 'digest':
                    bad['source']['sha256'] = '0' * 64
                else:
                    bad['unexpected'] = True
                write_selector(bad)
                with self.subTest(mutation=mutation), self.assertRaises(
                        current_components.CurrentComponentError):
                    current_components._select_current_lock(root)

    def test_resolver_matches_checked_out_gitlinks_and_archives(self):
        historical_lock = json.loads((ROOT / current_components.HISTORICAL_LOCK).read_text())
        historical = {item['path']: item['commit']
                      for item in historical_lock['components']}
        resolved = current_components.resolve_current_components(ROOT, historical)
        m20 = json.loads((ROOT / current_components.M20_LOCK).read_text())
        expected = {item['path']: item['commit'] for item in m20['components']
                    if item['path'] in current_components.EXPECTED_PATHS}
        self.assertEqual(resolved, expected)
        for path, commit in resolved.items():
            gitlink = subprocess.run(('git', 'rev-parse', 'HEAD:' + path), cwd=ROOT,
                                     check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(gitlink, commit)

    def test_m19_lock_rejects_a_component_that_does_not_descend_from_m17(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('manifests', 'components'):
                (root / name).mkdir()
            for name in ('components.lock.json', 'm17-components.lock.json'):
                shutil.copyfile(ROOT / 'manifests' / name, root / 'manifests' / name)
            lock = json.loads((ROOT / current_components.M19_LOCK).read_text())
            for item in lock['components']:
                if item['name'] == 'country':
                    item['commit'] = 'f' * 40
            (root / current_components.M19_LOCK).write_text(json.dumps(lock))
            for name in ('country', 'fdkernel', 'freecom'):
                (root / 'components' / name).symlink_to(ROOT / 'components' / name)
            with self.assertRaises(current_components.CurrentComponentError):
                current_components._resolve_m19(root)

    def test_m20_lock_binds_start_and_freedos_14_baseline(self):
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('manifests', 'components'):
                (root / name).mkdir()
            for name in ('components.lock.json', 'm19-components.lock.json'):
                shutil.copyfile(ROOT / 'manifests' / name, root / 'manifests' / name)
            for name in ('country', 'fdkernel', 'freecom'):
                (root / 'components' / name).symlink_to(ROOT / 'components' / name)
            original = json.loads((ROOT / current_components.M20_LOCK).read_text())
            (root / current_components.M20_LOCK).write_text(json.dumps(original))
            self.assertEqual(set(current_components._resolve_m20(root)),
                             current_components.EXPECTED_PATHS)
            # lpproj PC-98 history from 2015 does not descend from ke2043.
            for mutation in ('start', 'not-baseline', 'repository', 'archive'):
                lock = copy.deepcopy(original)
                kernel = next(i for i in lock['components'] if i['name'] == 'fdkernel')
                if mutation == 'start':
                    lock['start_sha'] = current_components.M19_START_SHA
                elif mutation == 'not-baseline':
                    kernel['commit'] = 'b883d1373' + subprocess.run(
                        ('git', 'rev-parse', 'b883d1373'), cwd=ROOT / 'components/fdkernel',
                        check=True, capture_output=True, text=True).stdout.strip()[9:]
                elif mutation == 'repository':
                    kernel['repository'] = 'https://github.com/lpproj/fdkernel.git'
                else:
                    kernel['source_archive_sha256'] = 'bad'
                (root / current_components.M20_LOCK).write_text(json.dumps(lock))
                with self.subTest(mutation=mutation), self.assertRaises(
                        current_components.CurrentComponentError):
                    current_components._resolve_m20(root)


if __name__ == '__main__':
    unittest.main()
