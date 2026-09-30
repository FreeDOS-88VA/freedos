# SPDX-License-Identifier: GPL-2.0-or-later
import json
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m18/qa'))
import workspace_readback as qa
from workspace_readback import check_stages


class WorkspaceReadbackTests(unittest.TestCase):
    def fixtures(self):
        base = {'HELLO.ASM': b'original', 'MZDEMO.ASM': b'mz source', 'BUILD.BAT': b'build'}
        extra = ('WORK/HELLO.ASM', 'WORK/MZDEMO.ASM', 'WORK/BUILD.BAT')
        copy = dict(base, **{name: base[name[5:]] for name in extra})
        edited = dict(copy, **{'WORK/HELLO.ASM': b'edited', 'WORK/HELLO.BAK': b'original'})
        mz = bytearray(32)
        mz[:2] = b'MZ'
        mz[6:8] = b'\x01\x00'
        built = dict(edited, **{'WORK/HELLO.COM': b'\xb8\x00L\xcd!', 'WORK/MZDEMO.EXE': bytes(mz)})

        def stage(files, free, work):
            return ({'fat_copies_equal': True, 'free_clusters': list(range(free)),
                     'files': {name: {'clusters': [2]} for name in files},
                     'directories': {'WORK': {}} if work else {}}, files)

        return [stage(base, 200, False), stage(copy, 196, True),
                stage(edited, 195, True), stage(built, 193, True)]

    def test_measures_only_valid_guest_stages_and_preserves_sources(self):
        stages = self.fixtures()
        result = check_stages(stages, 32, 128)
        self.assertEqual([row['additional_allocated_clusters'] for row in result], [0, 4, 5, 7])
        self.assertEqual(result[-1]['workspace_files']['WORK/MZDEMO.EXE']['bytes'], 32)

    def test_cli_rejects_manifest_drift_and_public_evidence_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / 'candidate.d88'
            image.write_bytes(b'synthetic candidate')
            manifest = root / 'build-manifest.json'
            manifest.write_text(json.dumps({'distribution_d88': {
                'sha256': '0' * 64, 'size_bytes': image.stat().st_size}}))
            args = ['workspace_readback.py']
            for step in ('normal', 'copy', 'edit', 'build'):
                args += ['--' + step, str(image)]
            args += ['--manifest', str(manifest), '--output', str(root / 'evidence.json')]
            with patch('sys.argv', args), self.assertRaisesRegex(ValueError, 'exact source build manifest'):
                qa.main()
            args[-1] = str(ROOT / 'private-evidence.json')
            with patch('sys.argv', args), self.assertRaisesRegex(ValueError, 'outside the public repository'):
                qa.main()
            self.assertFalse((root / 'evidence.json').exists())

    def test_missing_stage_or_corrupted_root_is_rejected(self):
        stages = self.fixtures()
        with self.assertRaisesRegex(ValueError, 'lacks both generated'):
            missing = self.fixtures()
            del missing[3][1]['WORK/HELLO.COM']
            del missing[3][0]['files']['WORK/HELLO.COM']
            check_stages(missing, 32, 128)
        with self.assertRaisesRegex(ValueError, 'root'):
            changed = self.fixtures()
            changed[2][1]['HELLO.ASM'] = b'changed'
            check_stages(changed, 32, 128)
        with self.assertRaisesRegex(ValueError, 'backup'):
            changed = self.fixtures()
            changed[2][1]['WORK/HELLO.BAK'] = b'bad'
            check_stages(changed, 32, 128)
        with self.assertRaisesRegex(ValueError, 'reserve'):
            check_stages(stages, 6, 128)
        with self.assertRaisesRegex(ValueError, 'stages'):
            check_stages(stages[:3], 32, 128)


if __name__ == '__main__':
    unittest.main()
