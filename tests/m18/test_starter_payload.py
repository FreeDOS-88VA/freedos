# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed checks for the original 8.3 ASCII assembler workflow."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = ROOT / "config/m18/payload"


class StarterPayloadTests(unittest.TestCase):
    def test_files_are_ascii_and_83(self):
        expected = {"BUILD.BAT", "HELLO.ASM", "MZDEMO.ASM",
                    "QUICKSTR.TXT", "README.TXT"}
        self.assertEqual({path.name for path in PAYLOAD.iterdir()}, expected)
        for name in expected:
            stem, dot, extension = name.partition(".")
            self.assertLessEqual(len(stem), 8)
            self.assertLessEqual(len(extension), 3)
            self.assertTrue(dot)
            self.assertTrue((PAYLOAD / name).read_bytes().isascii())

    def test_com_and_mz_examples_select_8086_and_no_linker(self):
        com = (PAYLOAD / "HELLO.ASM").read_text(encoding="ascii")
        mz = (PAYLOAD / "MZDEMO.ASM").read_text(encoding="ascii")
        batch = (PAYLOAD / "BUILD.BAT").read_text(encoding="ascii")
        self.assertRegex(com, r"(?im)^\.8086\s*$")
        self.assertRegex(com, r"(?im)^\.model\s+tiny\s*$")
        self.assertRegex(com, r"(?im)^org\s+100h\s*$")
        self.assertRegex(mz, r"(?im)^\.8086\s*$")
        self.assertRegex(mz, r"(?im)^\.model\s+small\s*$")
        self.assertRegex(mz, r"(?im)^\.stack\s+512\s*$")
        self.assertIn("@data", mz)
        self.assertIn("int 21h", com.lower())
        self.assertIn("int 21h", mz.lower())
        self.assertNotRegex(com + mz, r"(?im)^\s*int\s+(10h|13h|16h)\b")
        self.assertIn("JWASMR -0 -bin -Fo=HELLO.COM HELLO.ASM", batch)
        self.assertIn("JWASMR -0 -mz -Fo=MZDEMO.EXE MZDEMO.ASM", batch)
        self.assertNotIn("WLINK", batch.upper())
        self.assertNotIn("TLINK", batch.upper())

    def test_batch_deletes_old_products_before_build_and_checks_results(self):
        batch = (PAYLOAD / "BUILD.BAT").read_text(encoding="ascii").splitlines()
        hello_asm = batch.index("JWASMR -0 -bin -Fo=HELLO.COM HELLO.ASM")
        mz_asm = batch.index("JWASMR -0 -mz -Fo=MZDEMO.EXE MZDEMO.ASM")
        self.assertLess(batch.index("IF EXIST HELLO.COM DEL HELLO.COM"), hello_asm)
        self.assertLess(batch.index("IF EXIST MZDEMO.EXE DEL MZDEMO.EXE"), hello_asm)
        hello_check = batch.index("IF NOT EXIST HELLO.COM GOTO FAILED")
        hello_run = batch.index("HELLO.COM", hello_check + 1)
        mz_check = batch.index("IF NOT EXIST MZDEMO.EXE GOTO FAILED")
        mz_run = batch.index("MZDEMO.EXE", mz_check + 1)
        self.assertLess(hello_check, mz_asm)
        self.assertLess(mz_check, hello_run)
        self.assertLess(mz_check, mz_run)
        self.assertIn("MEMMAP /CHECK", batch)
        self.assertIn("IF ERRORLEVEL 1 GOTO FAILED", batch)

    def test_quickstart_documents_edlin_backup_and_both_formats(self):
        guide = (PAYLOAD / "QUICKSTR.TXT").read_text(encoding="ascii")
        self.assertIn("HELLO.BAK", guide)
        self.assertIn("Enter lowercase e to save", guide)
        self.assertIn("JWASMR -0 -bin", guide)
        self.assertIn("JWASMR -0 -mz", guide)
        self.assertIn("B:", guide)
        self.assertIn("MEMMAP /CHECK", guide)


if __name__ == "__main__":
    unittest.main()
