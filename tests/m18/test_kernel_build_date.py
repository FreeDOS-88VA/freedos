# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
from unittest.mock import patch
from tools.m18 import kernel_cc


class KernelDateTests(unittest.TestCase):
    def test_utc_fixed_width_definition_is_not_the_current_date(self):
        self.assertEqual(kernel_cc.date_definition(0), '-dKERNEL_BUILD_DATE="Jan  1 1970"')
        self.assertEqual(kernel_cc.banner_date(1787814827), 'Aug 27 2026')
        with patch.dict('os.environ', {'TZ': 'Pacific/Honolulu', 'LC_ALL': 'ja_JP.UTF-8'}):
            self.assertEqual(kernel_cc.banner_date(1787814827), 'Aug 27 2026')

    def test_wrapper_preserves_separate_stack_and_all_other_flags(self):
        arguments = ['kernel_cc.py', '-0', '-mm', '-zu', '-fo=main.obj', '../kernel/main.c']
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '1787814827'}), \
                patch('sys.argv', arguments), patch.object(kernel_cc.os, 'execv') as execute:
            kernel_cc.main()
        execute.assert_called_once_with(kernel_cc.COMPILER,
            [kernel_cc.COMPILER, '-dKERNEL_BUILD_DATE="Aug 27 2026"', *arguments[1:]])

    def test_linked_banner_is_required_and_duplicates_or_drift_fail(self):
        fixed = b'prefix [compiled Aug 27 2026]\n suffix'
        kernel_cc.verify_banner(fixed, 1787814827)
        for data in (b'no date', fixed + fixed, b'[compiled Sep 29 2026]'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                kernel_cc.verify_banner(data, 1787814827)


if __name__ == '__main__':
    unittest.main()
