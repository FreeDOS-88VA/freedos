# SPDX-License-Identifier: GPL-2.0-or-later
"""M17 profile, fixture, inspector, range, assignment and provenance tests."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m17'))
from contracts import (ContractError, RangeError, UnsupportedProfileError,
                       assign_block_units, checked_device_range, fat_layout,
                       fat_type_for_clusters, load, validate_document,
                       validate_profile, volume_range_to_device_blocks)
from inspect_storage import (InconsistentMediaError, MalformedMediaError,
                             TruncatedMediaError, UnsupportedMediaError,
                             _chs_for_lba, _verify_manifest, inspect,
                             main as inspect_main)
from produce import build, produce
from verify_source_audit import verify


class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((ROOT / 'config/m17/media-profiles.json').read_text())
        cls.profiles = load(ROOT / 'config/m17/media-profiles.json')
        cls.by_name = {profile['name']: profile for profile in cls.profiles}

    @staticmethod
    def volume_file_offset(profile):
        return (profile['container']['header_bytes'] +
                profile['volume']['volume_start_device_blocks'] *
                profile['device']['block_bytes'])

    @staticmethod
    def fat_entry(data, profile, cluster):
        v = profile['volume']
        bps = v['logical_sector_bytes']
        origin = StorageTests.volume_file_offset(profile)
        offset = origin + v['reserved_sectors'] * bps
        bits = v['fat_bits']
        fat = data[offset:offset + fat_layout(profile)['fat_sectors'] * bps]
        if bits == 16:
            return int.from_bytes(fat[cluster * 2:cluster * 2 + 2], 'little')
        at = cluster + cluster // 2
        pair = int.from_bytes(fat[at:at + 2], 'little')
        return (pair >> 4 if cluster & 1 else pair) & 0xfff

    @staticmethod
    def set_fat_entry(data, profile, cluster, value):
        v = profile['volume']
        bps = v['logical_sector_bytes']
        origin = StorageTests.volume_file_offset(profile)
        fat_length = fat_layout(profile)['fat_sectors'] * bps
        first = origin + v['reserved_sectors'] * bps
        second = first + fat_length
        copies = (first, second)
        for base in copies:
            if v['fat_bits'] == 16:
                struct.pack_into('<H', data, base + cluster * 2, value)
            else:
                at = base + cluster + cluster // 2
                word = int.from_bytes(data[at:at + 2], 'little')
                if cluster & 1:
                    word = (word & 0x000f) | (value << 4)
                else:
                    word = (word & 0xf000) | value
                data[at:at + 2] = word.to_bytes(2, 'little')

    def test_inspector_cli_distinguishes_usage_unsupported_and_invalid_media(self):
        profile = self.by_name['scsi40-512-fat16']
        data, _ = build(profile)
        profiles_path = ROOT / 'config/m17/media-profiles.json'

        def invoke(*args):
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    code = inspect_main(list(args))
                except SystemExit as error:
                    code = error.code
            return code, stdout.getvalue(), stderr.getvalue()

        code, _, stderr = invoke('--profiles', str(profiles_path))
        self.assertEqual(code, 64)
        self.assertIn('usage:', stderr)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.hdd'
            path.write_bytes(data)
            code, output, _ = invoke('--profiles', str(profiles_path),
                                     '--input', str(path), '--profile', profile['name'])
            self.assertEqual(code, 0)
            self.assertIn('valid-supported', output)
            unsupported = bytearray(data)
            unsupported[220 + 450] = 0x07
            path.write_bytes(unsupported)
            code, _, stderr = invoke('--profiles', str(profiles_path),
                                     '--input', str(path), '--profile', profile['name'])
            self.assertEqual(code, 2)
            self.assertIn('valid-but-unsupported', stderr)
            path.write_bytes(data[:-1])
            code, _, stderr = invoke('--profiles', str(profiles_path),
                                     '--input', str(path), '--profile', profile['name'])
            self.assertEqual(code, 3)
            self.assertIn('malformed/truncated', stderr)

    def test_profile_set_builds_and_inspects_byte_identically(self):
        self.assertEqual(len(self.profiles), 6)
        for profile in self.profiles:
            with self.subTest(profile=profile['name']):
                first, first_record = build(profile)
                second, second_record = build(profile)
                self.assertEqual(first, second)
                self.assertEqual(first_record, second_record)
                result = inspect(first, profile)
                self.assertEqual(result['files'], first_record['files'])
                self.assertEqual(result['cluster_count'], first_record['cluster_count'])
                self.assertEqual(result['fat_sectors_per_copy'],
                                 first_record['fat_sectors_per_copy'])
                self.assertEqual(result['volume_offset_bytes'],
                                 first_record['volume_offset_bytes'])
                self.assertFalse(profile['deployment']['bootable_fixture'])
                self.assertEqual(profile['qualification']['guest'], 'NOT_QUALIFIED')
                self.assertEqual(profile['qualification']['hardware'], 'NOT_RUN')

    def test_schema_file_binds_the_executable_contract_shape(self):
        from jsonschema import Draft202012Validator, FormatChecker
        schema = json.loads((ROOT / 'config/m17/media-profiles.schema.json').read_text())
        from jsonschema.exceptions import SchemaError
        Draft202012Validator.check_schema(schema)
        invalid_schema = copy.deepcopy(schema)
        invalid_schema['type'] = 'not-a-json-schema-type'
        with self.assertRaises(SchemaError):
            Draft202012Validator.check_schema(invalid_schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        validator.validate(self.document)
        self.assertEqual(schema['$schema'], 'https://json-schema.org/draft/2020-12/schema')
        self.assertEqual(schema['$id'], 'urn:pc88va:m17:media-profiles:v2')
        self.assertTrue(schema['additionalProperties'] is False)
        self.assertEqual(set(schema['required']),
                         {'schema_version', 'contract_id', 'evidence', 'profiles'})
        self.assertEqual(schema['properties']['schema_version'], {'const': 2})
        profile_schema = schema['$defs']['profile']
        self.assertFalse(profile_schema['additionalProperties'])
        self.assertEqual(set(profile_schema['required']), {
            'name', 'container', 'deployment', 'device', 'volume',
            'qualification', 'evidence_refs'})
        volume_schema = schema['$defs']['volume']
        self.assertIn('bpb_sectors_per_track', volume_schema['properties'])
        self.assertIn('bpb_heads', volume_schema['properties'])

    def test_schema_rejects_unknown_missing_and_malformed_instances(self):
        from jsonschema import Draft202012Validator, FormatChecker
        schema = json.loads((ROOT / 'config/m17/media-profiles.schema.json').read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        cases = []
        bad = copy.deepcopy(self.document)
        bad['unknown'] = True
        cases.append(('unknown root field', bad))
        bad = copy.deepcopy(self.document)
        bad['schema_version'] = True
        cases.append(('boolean schema version', bad))
        bad = copy.deepcopy(self.document)
        del bad['profiles'][0]['volume']['fat_bits']
        cases.append(('missing required field', bad))
        bad = copy.deepcopy(self.document)
        bad['evidence']['vaeg-storage-m16']['commit'] = 'g' * 40
        cases.append(('malformed commit', bad))
        for label, document in cases:
            with self.subTest(label=label):
                self.assertFalse(validator.is_valid(document))

    def test_schema_and_cross_field_negatives_fail_closed(self):
        cases = []
        bad = copy.deepcopy(self.document)
        bad['extra'] = 1
        cases.append(('unknown root field', bad))
        bad = copy.deepcopy(self.document)
        bad['schema_version'] = True
        cases.append(('boolean schema version', bad))
        bad = copy.deepcopy(self.document)
        del bad['profiles'][0]['volume']['fat_bits']
        cases.append(('missing profile field', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][0]['volume']['extra'] = 1
        cases.append(('unknown nested field', bad))
        bad = copy.deepcopy(self.document)
        bad['evidence']['vaeg-storage-m16']['commit'] = 'a' * 39
        cases.append(('short source hash', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][0]['evidence_refs'] = ['missing-source']
        cases.append(('unclosed evidence ref', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][0]['device']['heads'] = True
        cases.append(('boolean geometry', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][0]['device']['block_count'] += 1
        cases.append(('capacity/geometry drift', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][-1]['deployment']['permitted_boot_sources'] = ['SCSI']
        cases.append(('SCSI boot forbidden', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][-1]['deployment']['kind'] = 'kernel-builtin'
        cases.append(('controller ownership drift', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][-1]['volume']['volume_start_device_blocks'] += 1
        cases.append(('512-byte/physical-block conversion drift', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][-1]['volume']['hidden_sectors'] += 1
        cases.append(('hidden-sector drift', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][-1]['volume']['partition_entries'] = 2
        cases.append(('partition count outside selected set', bad))
        bad = copy.deepcopy(self.document)
        bad['profiles'][-1]['qualification']['hardware'] = 'HARDWARE PASS'
        cases.append(('unearned hardware status', bad))
        for label, document in cases:
            with self.subTest(label=label), self.assertRaises(ContractError):
                validate_document(document)

    def test_profile_validator_rejects_boolean_and_unknown_values(self):
        profile = self.by_name['fdd-360-fat12']
        for path, value in (
                (('device', 'native_unit'), True),
                (('device', 'heads'), False),
                (('volume', 'volume_serial'), True),
                (('volume', 'sectors_per_cluster'), 3),
                (('volume', 'logical_sector_bytes'), 256),
                (('volume', 'fat_bits'), 32),
                (('volume', 'root_entries'), 17),
                (('container', 'format'), 'unknown'),
                (('name',), '../escape')):
            bad = copy.deepcopy(profile)
            target = bad
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path, value=value), self.assertRaises(ContractError):
                validate_profile(bad)
        bad = copy.deepcopy(profile)
        del bad['volume']['hidden_sectors']
        with self.assertRaises(ContractError):
            validate_profile(bad)

    def test_duplicate_json_keys_and_profile_identity_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'profiles.json'
            path.write_text('{"schema_version":2,"schema_version":2}')
            with self.assertRaises(ContractError):
                load(path)
        bad = copy.deepcopy(self.document)
        bad['profiles'][0]['name'] = bad['profiles'][1]['name']
        with self.assertRaises(ContractError):
            validate_document(bad)
        bad = copy.deepcopy(self.document)
        bad['profiles'].pop()
        with self.assertRaises(ContractError):
            validate_document(bad)

    def test_fat_cluster_classification_boundaries(self):
        self.assertEqual(fat_type_for_clusters(4084), 12)
        self.assertEqual(fat_type_for_clusters(4085), 16)
        self.assertEqual(fat_type_for_clusters(4086), 16)
        self.assertEqual(fat_type_for_clusters(65524), 16)
        self.assertEqual(fat_type_for_clusters(65525), 32)
        with self.assertRaises(ContractError):
            fat_type_for_clusters(True)

    def test_lba_count_conversion_and_boundary_matrix(self):
        self.assertEqual(checked_device_range(0, 1, 10), (0, 1))
        self.assertEqual(checked_device_range(9, 1, 10), (9, 10))
        self.assertEqual(checked_device_range(0, 10, 10), (0, 10))
        for args in ((10, 1, 10), (9, 2, 10), (0, 0, 10),
                     (0xffffffff, 2, 0xffffffff), (True, 1, 10)):
            with self.subTest(args=args), self.assertRaises(RangeError):
                checked_device_range(*args)

        sasi = self.by_name['sasi40-fat16']
        self.assertEqual(volume_range_to_device_blocks(
            0, 1, 81178, 512, 256, 4, 162360), (4, 2))
        self.assertEqual(volume_range_to_device_blocks(
            sasi['volume']['total_logical_sectors'] - 1, 1,
            sasi['volume']['total_logical_sectors'], 512, 256, 4,
            sasi['device']['block_count']), (162358, 2))
        scsi256 = self.by_name['scsi40-256-fat16']
        self.assertEqual(volume_range_to_device_blocks(
            0, 1, 79872, 512, 256, 4096, 163840), (4096, 2))
        self.assertEqual(volume_range_to_device_blocks(
            79871, 1, 79872, 512, 256, 4096, 163840), (163838, 2))
        scsi512 = self.by_name['scsi40-512-fat16']
        self.assertEqual(volume_range_to_device_blocks(
            79871, 1, 79872, 512, 512, 2048, 81920), (81919, 1))
        fdd = self.by_name['fdd-1280-fat12']
        self.assertEqual(volume_range_to_device_blocks(
            1279, 1, 1280, 1024, 1024, 0, 1280), (1279, 1))
        for args in (
                (79872, 1, 79872, 512, 256, 4096, 163840),
                (79871, 1, 79872, 512, 256, 4096, 163839),
                (0, 1, 1280, 512, 1024, 0, 1280),
                (0xffffffff, 2, 0xffffffff, 1024, 512, 0, 81920),
                (0, 0, 79872, 512, 256, 0, 81920),
                (True, 1, 79872, 512, 256, 0, 81920)):
            with self.subTest(args=args), self.assertRaises(RangeError):
                volume_range_to_device_blocks(*args)

    def test_drive_assignment_is_stable_and_bounded_by_lastdrive(self):
        base = assign_block_units()
        self.assertEqual([row['drive'] for row in base], ['A', 'B'])
        one_sasi = assign_block_units(sasi_units=[0])
        self.assertEqual(one_sasi[2], {'dos_unit': 2, 'drive': 'C',
                                      'owner': 'sasi', 'native_unit': 0})
        two_sasi = assign_block_units(sasi_units=[0, 1])
        self.assertEqual([row['drive'] for row in two_sasi], ['A', 'B', 'C', 'D'])
        scsi_only = assign_block_units(scsi_units=[0])
        self.assertEqual(scsi_only[-1]['drive'], 'C')
        combined = assign_block_units(sasi_units=[0, 1], scsi_units=[0], lastdrive='E')
        self.assertEqual([row['drive'] for row in combined], ['A', 'B', 'C', 'D', 'E'])
        self.assertEqual(combined[-1]['owner'], 'scsi')
        for args in (
                {'sasi_units': [0, 1], 'scsi_units': [0], 'lastdrive': 'D'},
                {'sasi_units': [0, 0]}, {'scsi_units': [7]},
                {'lastdrive': 'B'}):
            with self.subTest(args=args), self.assertRaises(ContractError):
                assign_block_units(**args)

    def test_hdi_and_vhd_payload_bindings(self):
        for name in ('sasi40-fat12', 'scsi40-256-fat16', 'scsi40-512-fat16'):
            profile = self.by_name[name]
            data, record = build(profile)
            self.assertEqual(record['payload_bytes'],
                             profile['device']['block_count'] * profile['device']['block_bytes'])
            self.assertEqual(record['volume_offset_bytes'],
                             profile['container']['header_bytes'] +
                             profile['volume']['volume_start_device_blocks'] *
                             profile['device']['block_bytes'])
            self.assertEqual(inspect(data, profile)['container_header_bytes'],
                             profile['container']['header_bytes'])

    def test_valid_but_unsupported_is_distinct_from_malformed(self):
        scsi = self.by_name['scsi40-512-fat16']
        data, _ = build(scsi)
        outside = copy.deepcopy(scsi)
        outside['device']['block_bytes'] = 128
        with self.assertRaises(UnsupportedMediaError):
            inspect(data, outside)
        unknown_type = bytearray(data)
        unknown_type[220 + 446 + 4] = 0x07
        with self.assertRaises(UnsupportedMediaError):
            inspect(bytes(unknown_type), scsi)
        bootable_partition = bytearray(data)
        bootable_partition[220 + 446] = 0x80
        with self.assertRaises(UnsupportedMediaError):
            inspect(bytes(bootable_partition), scsi)
        fat32_label_only = bytearray(data)
        volume = self.volume_file_offset(scsi)
        fat32_label_only[volume + 54:volume + 62] = b'FAT32   '
        with self.assertRaises(InconsistentMediaError):
            inspect(bytes(fat32_label_only), scsi)

    def test_truncated_malformed_inconsistent_and_preserved_inputs(self):
        profile = self.by_name['fdd-360-fat12']
        data, _ = build(profile)
        with self.assertRaises(TruncatedMediaError):
            inspect(data[:-1], profile)
        with self.assertRaises(InconsistentMediaError):
            inspect(data + b'X', profile)
        for offset, value in ((13, 3), (14, 0), (16, 1), (21, 0),
                              (22, 0), (28, 1), (62, 0)):
            changed = bytearray(data)
            changed[offset] = value
            with self.subTest(offset=offset), self.assertRaises(InconsistentMediaError):
                inspect(bytes(changed), profile)
        for offset, value in ((11, 1), (510, 0)):
            changed = bytearray(data)
            changed[offset] = value
            with self.subTest(offset=offset), self.assertRaises(MalformedMediaError):
                inspect(bytes(changed), profile)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'readonly.img'
            path.write_bytes(data)
            path.chmod(0o444)
            before_mode = path.stat().st_mode
            before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            inspect(path.read_bytes(), profile)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before_hash)
            self.assertEqual(path.stat().st_mode, before_mode)

    def test_fat_corruption_and_directory_boundary_negatives(self):
        profile = self.by_name['fdd-360-fat12']
        original, _ = build(profile)
        v = profile['volume']
        bps = v['logical_sector_bytes']
        origin = self.volume_file_offset(profile)
        layout = fat_layout(profile)
        fat_offset = origin + v['reserved_sectors'] * bps
        fat_length = layout['fat_sectors'] * bps
        root_offset = origin + (v['reserved_sectors'] + 2 * layout['fat_sectors']) * bps
        corruptions = ('mirror', 'loop', 'orphan', 'crosslink', 'oversize',
                       'payload', 'fat-extent')
        for kind in corruptions:
            data = bytearray(original)
            if kind == 'mirror':
                data[fat_offset + 8] ^= 1
            elif kind == 'loop':
                self.set_fat_entry(data, profile, 2, 2)
            elif kind == 'orphan':
                free = next(cluster for cluster in range(2, layout['cluster_count'] + 2)
                            if self.fat_entry(data, profile, cluster) == 0)
                self.set_fat_entry(data, profile, free, 0xfff)
            elif kind == 'crosslink':
                readme = int.from_bytes(data[root_offset + 32 + 26:
                                               root_offset + 32 + 28], 'little')
                struct.pack_into('<H', data, root_offset + 64 + 26, readme)
            elif kind == 'oversize':
                struct.pack_into('<I', data, root_offset + 64 + 28, 0xffffffff)
            elif kind == 'payload':
                first_cluster = int.from_bytes(data[root_offset + 32 + 26:
                                                     root_offset + 32 + 28], 'little')
                cluster_bytes = v['sectors_per_cluster'] * bps
                data[origin + layout['data_start_sector'] * bps +
                     (first_cluster - 2) * cluster_bytes] ^= 1
            elif kind == 'fat-extent':
                beyond = layout['cluster_count'] + 2
                self.set_fat_entry(data, profile, beyond, 0xfff)
            with self.subTest(kind=kind), self.assertRaises(InconsistentMediaError):
                inspect(bytes(data), profile)

    def test_mbr_overlap_chs_lba_and_partition_boundaries(self):
        profile = self.by_name['scsi40-256-fat16']
        original, _ = build(profile)
        base = profile['container']['header_bytes']
        mutations = []
        changed = bytearray(original)
        changed[base + 510] = 0
        mutations.append(('signature', changed, MalformedMediaError))
        changed = bytearray(original)
        changed[base + 446 + 1] ^= 1
        mutations.append(('chs-lba-disagreement', changed, InconsistentMediaError))
        changed = bytearray(original)
        struct.pack_into('<I', changed, base + 446 + 8, 2049)
        mutations.append(('wrong-partition-start', changed, InconsistentMediaError))
        changed = bytearray(original)
        struct.pack_into('<I', changed, base + 446 + 12, 0xffffffff)
        mutations.append(('partition-overrun', changed, InconsistentMediaError))
        for label, data, error in mutations:
            with self.subTest(label=label), self.assertRaises(error):
                inspect(bytes(data), profile)

        valid_multiple = bytearray(original)
        struct.pack_into('<I', valid_multiple, base + 446 + 12, 40000)
        valid_multiple[base + 446 + 5:base + 446 + 8] = _chs_for_lba(42047, 32, 8)
        second = base + 462
        struct.pack_into('<B3sB3sII', valid_multiple, second, 0,
                         _chs_for_lba(42048, 32, 8), 0x06,
                         _chs_for_lba(81919, 32, 8), 42048, 39872)
        with self.assertRaises(UnsupportedMediaError):
            inspect(bytes(valid_multiple), profile)
        overlap = bytearray(original)
        second = base + 462
        struct.pack_into('<B3sB3sII', overlap, second, 0,
                         _chs_for_lba(3000, 32, 8), 0x06,
                         _chs_for_lba(3099, 32, 8), 3000, 100)
        with self.assertRaises(InconsistentMediaError):
            inspect(bytes(overlap), profile)

    def test_container_header_truncation_and_profile_classification(self):
        for name in ('sasi40-fat12', 'scsi40-512-fat16'):
            profile = self.by_name[name]
            data, _ = build(profile)
            with self.assertRaises(TruncatedMediaError):
                inspect(data[:-1], profile)
            changed = bytearray(data)
            changed[profile['container']['header_bytes'] - 1] ^= 1
            with self.assertRaises(InconsistentMediaError):
                inspect(bytes(changed), profile)

    def test_manifest_identity_semantics_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'run'
            manifest = produce(ROOT / 'config/m17/media-profiles.json', output)
            self.assertEqual(manifest['schema_version'], 2)
            results = _verify_manifest(output, self.profiles)
            self.assertEqual(len(results), 6)
            before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in output.iterdir() if path.is_file()}
            with self.assertRaises(FileExistsError):
                produce(ROOT / 'config/m17/media-profiles.json', output)
            after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in output.iterdir() if path.is_file()}
            self.assertEqual(before, after)

            manifest_path = output / 'manifest.json'
            valid = json.loads(manifest_path.read_text())
            for mutate in (
                    lambda value: value['fixtures'][0].update(sha256='0' * 64),
                    lambda value: value['fixtures'][0].update(extra=1),
                    lambda value: value['fixtures'].pop(),
                    lambda value: value['fixtures'].reverse()):
                bad = copy.deepcopy(valid)
                mutate(bad)
                manifest_path.write_text(json.dumps(bad))
                with self.assertRaises(InconsistentMediaError):
                    _verify_manifest(output, self.profiles)
            manifest_path.write_text(json.dumps(valid))
            fixture = output / valid['fixtures'][0]['file']
            original = fixture.read_bytes()
            fixture.write_bytes(original[:-1])
            with self.assertRaises(InconsistentMediaError):
                _verify_manifest(output, self.profiles)

    def test_mbrless_prefix_fdd_and_sasi_layouts(self):
        for name, prefix in (('fdd-360-fat12', 0), ('sasi40-fat16', 4 * 256)):
            profile = self.by_name[name]
            data, record = build(profile)
            header = profile['container']['header_bytes']
            if prefix:
                self.assertEqual(data[header:header + prefix], bytes(prefix))
                self.assertEqual(record['volume_offset_bytes'], header + prefix)
            else:
                self.assertEqual(data[:3], b'\xeb\x3c\x90')
                self.assertEqual(record['volume_offset_bytes'], 0)
            self.assertNotEqual(profile['volume']['partition_scheme'], 'mbr-primary')


class SourceAuditTests(unittest.TestCase):
    def test_source_binding_negatives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit = json.loads((ROOT / 'config/m17/source-audit.json').read_text())
            paths = ['config/m17/source-audit.json', 'manifests/m17-components.lock.json']
            paths += ['components/fdkernel/' + path for path in audit['files']]
            for path in paths:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            verify(root)
            destination = root / 'config/m17/source-audit.json'
            for mutation in ('kernel', 'unknown', 'missing', 'hash', 'content'):
                changed = copy.deepcopy(audit)
                if mutation == 'kernel':
                    changed['kernel_commit'] = '0' * 40
                elif mutation == 'unknown':
                    changed['files']['../other'] = '0' * 64
                elif mutation == 'missing':
                    del changed['files']['kernel/config.c']
                elif mutation == 'hash':
                    changed['files']['kernel/config.c'] = 'broken'
                else:
                    changed['files']['kernel/config.c'] = '0' * 64
                destination.write_text(json.dumps(changed))
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    verify(root)


if __name__ == '__main__':
    unittest.main()
