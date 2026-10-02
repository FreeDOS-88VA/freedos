# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('msdos4_readback', ROOT / 'tools/m19/qa/msdos4_readback.py')
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class ReadbackTests(unittest.TestCase):
    def fixture(self):
        base = {'HELLO.ASM': b'; synthetic source\r\n'}
        guest = dict(base)
        guest.update({'HZ.ASM': base['HELLO.ASM'], 'TYPE.TXT': base['HELLO.ASM'],
                      'VER.TXT': b'MS-DOS Version 6.22\r\n',
                      'PRE.TXT': b'MCB chain: VALID\r\n', 'POST.TXT': b'MCB chain: VALID\r\n',
                      'LAST.TXT': b'MCB chain: VALID\r\n',
                      'COPY.TXT': b'1 File(s) copied\r\n', 'ERR.TXT': b'File not found\r\n',
                      'RUNCOM.TXT': b'Hello from PC-88VA FreeDOS!\r\n',
                      'RUNMZ.TXT': b'MZ relocation and DOS return succeeded.\r\n',
                      'ASMCOM.TXT': b'0 errors', 'ASMMZ.TXT': b'0 errors',
                      'HELLO.COM': b'\xcd\x20'})
        for name, value in [('ENV', 'OK'), ('FOR', 'ONE\r\nTWO'), ('EXIST', 'COPYOK'),
                            ('PIPE', 'PIPEOK'), ('CHILD', 'CHILDOK'), ('CALL', 'CALLOK'),
                            ('BATCH', 'BATCHOK'), ('DONE', 'FINISHED')]:
            guest[name + '.TXT'] = (value + '\r\n').encode()
        mz = bytearray(28)
        mz[:2] = b'MZ'
        struct.pack_into('<H', mz, 6, 1)
        guest['MZDEMO.EXE'] = bytes(mz)
        return base, guest

    def test_complete_fixture(self):
        self.assertTrue(qa.check(*self.fixture())['mcb_checks_before_after'])

    def test_missing_outputs_and_payload_drift_fail(self):
        base, guest = self.fixture()
        for name in list(guest):
            broken = dict(guest)
            del broken[name]
            with self.subTest(name=name), self.assertRaises(ValueError):
                qa.check(base, broken)
        guest['HELLO.ASM'] += b'changed'
        with self.assertRaises(ValueError):
            qa.check(base, guest)

    def test_false_success_version_corruption_and_executables_fail(self):
        base, guest = self.fixture()
        for name, value in [('VER.TXT', b'4.00'), ('POST.TXT', b'invalid chain'),
                            ('RUNCOM.TXT', b'not run'), ('PIPE.TXT', b'wrong'),
                            ('HELLO.COM', b''), ('MZDEMO.EXE', b'MZ'), ('BAD.TXT', b'')]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                qa.check(base, dict(guest, **{name: value}))


if __name__ == '__main__':
    unittest.main()
