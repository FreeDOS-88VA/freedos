# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed unit regressions for M17 build acceptance metadata."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / 'tools/m17'))
from verify_acceptance import (AcceptanceError, BUILD_FIELDS, LINKED_GATES,
                               TEST_SUITES, read_json, validate_artifact_tree,
                               validate_build_record, validate_m17_lock,
                               validate_predecessor_ci, verify_build_log)


START_SHA = 'f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4'
GOOD_CI = [
    {'workflow': 'M16 isolated source build', 'run_id': 36381203803,
     'attempt': 1, 'head_sha': START_SHA, 'conclusion': 'success'},
    {'workflow': 'M16 scaffold', 'run_id': 36381203807,
     'attempt': 1, 'head_sha': START_SHA, 'conclusion': 'success'},
]


def build_record():
    return {
        'sources': {name: '1' * 40 for name in
                    ('parent', 'fdkernel', 'freecom', 'country')},
        'source_archives_sha256': {name: '2' * 64 for name in
                                   ('parent', 'fdkernel', 'freecom', 'country')},
        'toolchain_image': 'sha256:' + '3' * 64,
        'host_wheels_sha256': {name: '4' * 64 for name in (
            'unicorn', 'jsonschema', 'attrs', 'jsonschema-specifications',
            'referencing', 'rpds-py')},
        'vaeg_candidate': {},
        'two_clean_builds_equal': True,
        'artifacts': {'media.d88': {'size': 1, 'sha256': '5' * 64}},
        'guest_boot': 'NOT RUN',
        'hardware': 'NOT RUN',
    }


def complete_log():
    lines = [
        'M17 build export is isolated from other milestones',
        'M17 reviewed sources match pinned kernel',
        *LINKED_GATES,
    ]
    for suite in TEST_SUITES:
        lines.extend(('M17_TEST_BEGIN ' + suite, 'M17_TEST_PASS ' + suite))
    return '\n'.join(lines) + '\n'


class AcceptanceTests(unittest.TestCase):
    def test_m17_lock_has_closed_shape_and_exact_historical_bindings(self):
        source = ROOT / 'manifests/m17-components.lock.json'
        valid = read_json(source)
        validate_m17_lock(valid, ROOT)
        mutations = []
        unknown = copy.deepcopy(valid)
        unknown['unreviewed'] = True
        mutations.append(unknown)
        nested = copy.deepcopy(valid)
        nested['components'][0]['future'] = 'unknown'
        mutations.append(nested)
        stale_ci = copy.deepcopy(valid)
        stale_ci['predecessor_ci'][0]['head_sha'] = '0' * 40
        mutations.append(stale_ci)
        historic = copy.deepcopy(valid)
        historic['historical_components_lock']['sha256'] = '0' * 64
        mutations.append(historic)
        stale_control = copy.deepcopy(valid)
        del stale_control['m15_control']['components']['components/country']
        mutations.append(stale_control)
        for lock in mutations:
            with self.subTest(lock=lock), self.assertRaises(AcceptanceError):
                validate_m17_lock(lock, ROOT)

    def test_build_record_requires_exact_fields_and_status_labels(self):
        validate_build_record(build_record())
        for mutation in ('missing', 'unknown', 'source', 'wheel', 'toolchain',
                         'guest', 'hardware', 'build-equality'):
            bad = copy.deepcopy(build_record())
            if mutation == 'missing':
                del bad['host_wheels_sha256']
            elif mutation == 'unknown':
                bad['extra'] = True
            elif mutation == 'source':
                bad['sources']['parent'] = 'bad'
            elif mutation == 'wheel':
                bad['host_wheels_sha256']['rpds-py'] = 'f' * 63
            elif mutation == 'toolchain':
                bad['toolchain_image'] = 'latest'
            elif mutation == 'guest':
                bad['guest_boot'] = 'PASS'
            elif mutation == 'hardware':
                bad['hardware'] = 'PASS'
            else:
                bad['two_clean_builds_equal'] = 1
            with self.subTest(mutation=mutation), self.assertRaises(AcceptanceError):
                validate_build_record(bad)
        self.assertEqual(set(build_record()), BUILD_FIELDS)

    def test_artifact_tree_matches_hash_size_and_exact_topology(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b'public synthetic artifact\n'
            (root / 'media.d88').write_bytes(data)
            (root / 'artifacts.json').write_text('{}\n')
            valid = {'media.d88': {'size': len(data),
                                   'sha256': hashlib.sha256(data).hexdigest()}}
            validate_artifact_tree(root, valid)
            (root / 'unexpected.bin').write_bytes(b'extra')
            with self.assertRaises(AcceptanceError):
                validate_artifact_tree(root, valid)
            (root / 'unexpected.bin').unlink()
            (root / 'media.d88').write_bytes(b'drift')
            with self.assertRaises(AcceptanceError):
                validate_artifact_tree(root, valid)

    def test_artifact_manifest_rejects_malformed_hash_size_fields_and_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'A.BIN').write_bytes(b'x')
            base = {'A.BIN': {'size': 1, 'sha256': hashlib.sha256(b'x').hexdigest()}}
            for mutate in (
                    lambda item: item['A.BIN'].update(sha256='z' * 64),
                    lambda item: item['A.BIN'].update(size=True),
                    lambda item: item['A.BIN'].update(extra=1),
                    lambda item: item.update({'../outside': {'size': 0, 'sha256': '0' * 64}}),
                    lambda item: item.update({'C:\\escape': {'size': 0, 'sha256': '0' * 64}})):
                bad = copy.deepcopy(base)
                mutate(bad)
                with self.subTest(manifest=bad), self.assertRaises(AcceptanceError):
                    validate_artifact_tree(root, bad)

    def test_artifact_tree_rejects_symlinks_and_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b'x'
            record = {'x.bin': {'size': 1, 'sha256': hashlib.sha256(data).hexdigest()}}
            with self.assertRaises(AcceptanceError):
                validate_artifact_tree(root, record)
            (root / 'x.bin').write_bytes(data)
            (root / 'alias.bin').symlink_to(root / 'x.bin')
            with self.assertRaises(AcceptanceError):
                validate_artifact_tree(root, record)

    def test_predecessor_ci_rejects_stale_head_run_attempt_and_unknown_claims(self):
        validate_predecessor_ci(GOOD_CI, START_SHA)
        mutations = []
        stale_head = copy.deepcopy(GOOD_CI)
        stale_head[0]['head_sha'] = '0' * 40
        mutations.append(stale_head)
        stale_run = copy.deepcopy(GOOD_CI)
        stale_run[1]['run_id'] += 1
        mutations.append(stale_run)
        stale_attempt = copy.deepcopy(GOOD_CI)
        stale_attempt[0]['attempt'] = 2
        mutations.append(stale_attempt)
        failed = copy.deepcopy(GOOD_CI)
        failed[1]['conclusion'] = 'failure'
        mutations.append(failed)
        extra = copy.deepcopy(GOOD_CI)
        extra[0]['comment'] = 'stale'
        mutations.append(extra)
        incomplete = GOOD_CI[:1]
        mutations.append(incomplete)
        for claim in mutations:
            with self.subTest(claim=claim), self.assertRaises(AcceptanceError):
                validate_predecessor_ci(claim, START_SHA)

    def test_second_clean_build_log_requires_gates_but_no_redundant_test_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'build-2.log'
            path.write_text('\n'.join((
                'M17 build export is isolated from other milestones',
                'M17 reviewed sources match pinned kernel',
                *LINKED_GATES,
            )) + '\n')
            verify_build_log(path, tests_required=False)
            path.write_text(path.read_text() + 'M17_TEST_BEGIN storage\n')
            with self.assertRaises(AcceptanceError):
                verify_build_log(path, tests_required=False)

    def test_build_log_requires_every_named_suite_once_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'build.log'
            path.write_text(complete_log())
            verify_build_log(path)
            for mutate in (
                    lambda text: text.replace('M17_TEST_PASS storage\n', '', 1),
                    lambda text: text.replace('M17_TEST_PASS storage\n',
                                              'M17_TEST_PASS storage\nM17_TEST_PASS storage\n', 1),
                    lambda text: text.replace('M17_TEST_PASS acceptance\n',
                                              'M17_TEST_PASS stale\n', 1),
                    lambda text: text.replace(LINKED_GATES[0], '', 1)):
                path.write_text(mutate(complete_log()))
                with self.assertRaises(AcceptanceError):
                    verify_build_log(path)


if __name__ == '__main__':
    unittest.main()
