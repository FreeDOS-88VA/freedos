# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('kswap_readback', ROOT / 'tools/m19/qa/kswap_readback.py')
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class KswapReadbackTests(unittest.TestCase):
    def fixture(self):
        base = {'COMMAND.COM': b'synthetic shell', 'KSSF.COM': b'synthetic wrapper'}
        guest = dict(base)
        def record(paras, owners):
            return ('PSP allocation paragraphs: %04X\r\nLive COMMAND-named MCBs: %04X\r\n' % (paras, owners)).encode()
        guest['BASE.OUT'] = record(100, 2)
        guest['FIRST.OUT'] = record(200, 0)
        for i in range(20):
            guest['S%02d.OUT' % i] = record(200, 0)
        for name, value in [('ARGS.OUT', b'ARGUMENTS'), ('ENV.TXT', b'HELLO'),
                            ('ENV2.TXT', b'HELLO'), ('ALIAS.TXT', b'ALIASOK'),
                            ('ALIAS2.TXT', b'ALIASOK'), ('RC.TXT', b'7'),
                            ('ASMCOM.TXT', b'0'), ('ASMMZ.TXT', b'0'),
                            ('ALIAS3.TXT', b'ALIASOK'), ('ENV3.TXT', b'HELLO'),
                            ('DONE.TXT', b'FINISHED')]:
            guest[name] = value + b'\r\n'
        guest['HIST.TXT'] = b'set KEEP=HELLO\r\n'
        guest['HIST2.TXT'] = b'CALL /S JWASMR -0 -mz -Fo=MZDEMO.EXE MZDEMO.ASM\r\n'
        guest['MZ.OK'] = b'MZ relocation OK\r\n'
        for name in ('PRE.TXT', 'POST.TXT', 'LAST.TXT'):
            guest[name] = b'MCB chain: VALID\r\n'
        guest.update({'RUNCOM.TXT': b'Hello from PC-88VA FreeDOS!',
                      'RUNMZ.TXT': b'MZ relocation and DOS return succeeded.',
                      'HELLO.COM': b'compiled fixture'})
        mz = bytearray(28)
        mz[:2] = b'MZ'
        struct.pack_into('<H', mz, 6, 1)
        guest['MZDEMO.EXE'] = bytes(mz)
        return base, guest

    def test_public_producer_syntax_and_component_inspectors(self):
        path = ROOT / 'tools/m19/qa/kswap_media.py'
        compile(path.read_text(), str(path), 'exec')
        subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover',
                        '-s', str(ROOT / 'components/freecom/tests/kswap')],
                       cwd=ROOT / 'components/freecom', check=True)

    def test_guest_assembly_explicitly_borrows_memory_without_swapped_redirection(self):
        script = (ROOT / 'config/m19/kswap-guest-input.txt').read_text()
        self.assertIn('CALL /S JWASMR -0 -bin -Fo=HELLO.COM HELLO.ASM\n', script)
        self.assertIn('CALL /S JWASMR -0 -mz -Fo=MZDEMO.EXE MZDEMO.ASM\n', script)
        for name in ('ASMCOM.TXT', 'ASMMZ.TXT'):
            self.assertIn('ECHO %ERRORLEVEL% > ' + name, script)
        for line in script.splitlines():
            if line.startswith('CALL /S JWASMR'):
                self.assertNotIn('>', line)

    def test_complete(self):
        self.assertTrue(qa.check(*self.fixture())['checks_passed'])

    def test_missing_every_required_output_fails(self):
        base, guest = self.fixture()
        for name in guest:
            broken = dict(guest)
            del broken[name]
            with self.subTest(missing=name), self.assertRaises(ValueError):
                qa.check(base, broken)

    def test_corrupt_accounting_lost_state_and_payload_drift_fail(self):
        base, guest = self.fixture()
        for name, value in [('COMMAND.COM', b'changed'), ('KSSF.COM', b'changed'),
                            ('S00.OUT', guest['BASE.OUT']), ('S01.OUT', b'invalid'),
                            ('FIRST.OUT', guest['BASE.OUT']), ('ENV2.TXT', b'lost'),
                            ('RC.TXT', b'0'), ('ASMCOM.TXT', b'0 errors'),
                            ('ASMMZ.TXT', b'1'), ('ENV3.TXT', b'lost'),
                            ('ALIAS3.TXT', b'lost'), ('POST.TXT', b'invalid chain'),
                            ('LAST.TXT', b'changed MCB chain: VALID'),
                            ('MZ.OK', b'not executed'), ('DONE.TXT', b'not done'),
                            ('HIST.TXT', b'empty'), ('HIST2.TXT', b'empty'),
                            ('MZDEMO.EXE', b'MZ')]:
            with self.subTest(corrupt=name), self.assertRaises(ValueError):
                qa.check(base, dict(guest, **{name: value}))

    def test_nonzero_exit_does_not_allow_a_false_error_then_prompt(self):
        qa.check_screen(b'COMPLETED\nA:\\>\n')
        for text in (b'String #38\nA:\\>\n', b'PANIC\nA:\\>\n',
                     b'MCB chain corrupt, or MS-DOS incompatible system.\nA:\\>\n',
                     b'context is missing\nA:\\>\n', b'not returned'):
            with self.subTest(screen=text), self.assertRaises(ValueError):
                qa.check_screen(text)

    def test_probe_rejects_trailing_data_and_bad_topology(self):
        for data in (b'', b'PSP allocation paragraphs: 0000\n',
                     self.fixture()[1]['FIRST.OUT'] + b'PASS'):
            with self.assertRaises(ValueError):
                qa.probe(data)


if __name__ == '__main__':
    unittest.main()
