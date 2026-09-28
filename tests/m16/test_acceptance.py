# SPDX-License-Identifier: GPL-2.0-or-later
"""M16-local acceptance schema and fail-closed negative tests."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('m16_acceptance', ROOT/'tools/m16/verify_acceptance.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class AcceptanceSchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT/'config/m16/acceptance.schema.json').read_text())
        self.record = json.loads((ROOT/'config/m16/acceptance.json').read_text())
        gate.validate_schema(self.schema)
        gate.validate_instance(self.schema, self.record)

    def reject(self, code, callback):
        with self.assertRaises(gate.Rejected) as result:
            callback()
        self.assertEqual(str(result.exception), code)

    def test_schema_and_checked_in_candidate_are_valid(self):
        gate.validate_schema(self.schema)
        gate.validate_instance(self.schema, self.record)

    def test_publication_schema_and_instance_are_valid(self):
        schema = json.loads((ROOT/'config/m16/publication.schema.json').read_text())
        instance = {
            'schema_version': 1,
            'repository': 'nakatamaho/freedos-pc88va',
            'remote': 'origin',
            'branch': 'topic/m16-floppy-formats-console-input',
            'identities': {
                'START_SHA': '1' * 40,
                'QUALIFIED_IMPLEMENTATION_SHA': '2' * 40,
                'PUBLICATION_TIP_SHA': '3' * 40,
                'DOWNSTREAM_BASE_SHA': '4' * 40
            },
            'ci': [{
                'repository': 'nakatamaho/freedos-pc88va', 'run_id': 17,
                'attempt': 1, 'head_sha': '3' * 40,
                'workflow_path': '.github/workflows/m16-source-build.yml',
                'required_jobs': ['isolated-build']
            }]
        }
        gate.validate_schema(schema)
        gate.validate_instance(schema, instance)

    def test_distribution_schema_is_valid(self):
        schema = json.loads((ROOT/'config/m16/distribution.schema.json').read_text())
        gate.validate_schema(schema)

    def test_unknown_schema_keyword_fails_closed(self):
        schema = copy.deepcopy(self.schema)
        schema['properties']['status']['format'] = 'm16-status'
        self.reject('UNSUPPORTED_SCHEMA_KEYWORD', lambda: gate.validate_schema(schema))

    def test_invalid_schema_pattern_is_rejected(self):
        schema = {'type': 'string', 'pattern': '['}
        self.reject('INVALID_SCHEMA', lambda: gate.validate_schema(schema))

    def test_required_schema_keyword_must_have_valid_shape(self):
        schema = {'type': 'object', 'required': 'ready'}
        self.reject('INVALID_SCHEMA', lambda: gate.validate_schema(schema))

    def test_missing_required_field_is_rejected(self):
        record = copy.deepcopy(self.record)
        del record['components']['freecom']
        self.reject('INVALID_INSTANCE', lambda: gate.validate_instance(self.schema, record))

    def test_unknown_record_field_is_rejected(self):
        record = copy.deepcopy(self.record)
        record['private_trace'] = 'not allowed'
        self.reject('INVALID_INSTANCE', lambda: gate.validate_instance(self.schema, record))

    def test_bad_commit_identity_is_rejected_by_schema(self):
        record = copy.deepcopy(self.record)
        record['identities']['START_SHA'] = '1' * 39
        self.reject('INVALID_INSTANCE', lambda: gate.validate_instance(self.schema, record))

    def test_bad_digest_is_rejected_by_schema(self):
        record = copy.deepcopy(self.record)
        record['distribution']['archive_sha256'] = 'sha256:bad'
        self.reject('INVALID_INSTANCE', lambda: gate.validate_instance(self.schema, record))

    def test_complete_m16_and_handoff_statuses_are_accepted(self):
        record = copy.deepcopy(self.record)
        record['status'] = 'M16 PASS'
        record['gates']['M16_HANDOFF'] = 'HANDOFF READY'
        gate.validate_instance(self.schema, record)

    def test_unknown_handoff_status_is_rejected(self):
        record = copy.deepcopy(self.record)
        record['gates']['M16_HANDOFF'] = 'NOT RUN'
        self.reject('INVALID_INSTANCE', lambda: gate.validate_instance(self.schema, record))

    def test_hardware_cannot_be_claimed_as_pass(self):
        record = copy.deepcopy(self.record)
        record['hardware']['status'] = 'HARDWARE PASS'
        self.reject('INVALID_INSTANCE', lambda: gate.validate_instance(self.schema, record))

    def test_duplicate_json_field_is_rejected(self):
        self.reject('DUPLICATE_JSON_FIELD', lambda: gate.json_value('{"ready":true,"ready":false}'))

    def test_artifact_size_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'artifact.bin').write_bytes(b'expected')
            self.reject('ARTIFACT_SIZE_DRIFT', lambda: gate.bound_file(
                root, 'artifact.bin', expected_size=9))

    def test_artifact_digest_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'artifact.bin').write_bytes(b'expected')
            self.reject('ARTIFACT_DIGEST_DRIFT', lambda: gate.bound_file(
                root, 'artifact.bin', expected_sha='a' * 64))

    def test_parent_path_reference_is_rejected(self):
        self.reject('INVALID_ARTIFACT_PATH', lambda: gate.safe_file(ROOT, '../outside'))


class IdentityAndCiTests(unittest.TestCase):
    def reject(self, code, callback):
        with self.assertRaises(gate.Rejected) as result:
            callback()
        self.assertEqual(str(result.exception), code)

    def test_commit_and_digest_require_full_lowercase_hex(self):
        for value in ('a' * 39, 'A' * 40, '0' * 40, None):
            with self.assertRaises(gate.Rejected):
                gate.check_commit(value)
        for value in ('b' * 63, 'G' * 64, '0' * 64, None):
            with self.assertRaises(gate.Rejected):
                gate.check_digest(value)

    def test_duplicate_publication_identity_is_rejected(self):
        identities = ['1' * 40, '2' * 40, '3' * 40, '2' * 40]
        self.reject('IDENTITY_COLLISION', lambda: gate.verify_distinct_commits(identities))

    def test_missing_required_source_ci_head_is_rejected(self):
        claims = [{'head_sha': 'a' * 40}, {'head_sha': 'b' * 40}]
        self.reject('REQUIRED_SOURCE_CI_MISSING', lambda: gate.verify_required_ci_heads(
            claims, {'a' * 40, 'b' * 40, 'c' * 40}))

    def setUp(self):
        self.claim = {
            'repository': 'owner/repo', 'run_id': 42, 'attempt': 1,
            'head_sha': 'a' * 40, 'workflow_path': '.github/workflows/build.yml',
            'required_jobs': ['build']
        }
        self.run = {
            'repository': {'full_name': 'owner/repo'}, 'id': 42, 'run_attempt': 1,
            'head_sha': 'a' * 40, 'path': '.github/workflows/build.yml',
            'status': 'completed', 'conclusion': 'success'
        }
        self.jobs = [{'name': 'build', 'head_sha': 'a' * 40, 'conclusion': 'success'}]

    def test_exact_successful_ci_claim(self):
        gate.verify_ci_claim(self.claim, self.run, self.jobs)

    def test_stale_ci_head_is_rejected(self):
        run = dict(self.run, head_sha='c' * 40)
        with self.assertRaises(gate.Rejected) as result:
            gate.verify_ci_claim(self.claim, run, self.jobs)
        self.assertEqual(str(result.exception), 'CI_HEAD_SHA_DRIFT')

    def test_failed_job_is_rejected(self):
        jobs = [{'name': 'build', 'head_sha': 'a' * 40, 'conclusion': 'failure'}]
        with self.assertRaises(gate.Rejected) as result:
            gate.verify_ci_claim(self.claim, self.run, jobs)
        self.assertEqual(str(result.exception), 'CI_JOB_NOT_QUALIFIED')

    def test_wrong_publication_ancestry_is_rejected(self):
        failed = type('ProcessResult', (), {'returncode': 1})()
        with patch.object(gate.subprocess, 'run', return_value=failed):
            self.reject('ANCESTRY_MISMATCH', lambda: gate.verify_ancestry(
                Path('/not-used'), '1' * 40, '2' * 40))


if __name__ == '__main__':
    unittest.main()
