# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('msdos4_builder', ROOT / 'tools/m19/qa/build_msdos4.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class MsDos4BuilderTests(unittest.TestCase):
    def test_original_build_is_opt_out_and_va_requires_freedos(self):
        self.assertEqual(builder.assembler_definitions('original'), [])
        self.assertEqual(builder.assembler_definitions('pc88va'), ['/DFREEDOS', '/DPC88VA'])
        with self.assertRaises(KeyError):
            builder.assembler_definitions('unknown')

    def test_link_response_preserves_order_and_bounds_dos_lines(self):
        data = builder.link_response(builder.MODULES)
        self.assertTrue(data.endswith(b',COMMAND.EXE,COMMAND.MAP,;\r\n'))
        self.assertTrue(all(len(line) <= 127 for line in data.splitlines()))
        objects = data.decode().split(',')[0].replace('\r\n', '').split('+')
        self.assertEqual(objects, [m + '.OBJ' for m in builder.MODULES])

    def test_link_response_rejects_empty_duplicates_injection_and_overflow(self):
        for modules in ([], ['A', 'A'], ['A;B'], ['A' * 128]):
            with self.subTest(modules=modules), self.assertRaises(ValueError):
                builder.link_response(modules)


if __name__ == '__main__':
    unittest.main()
