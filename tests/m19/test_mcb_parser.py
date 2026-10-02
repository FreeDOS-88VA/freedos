# SPDX-License-Identifier: GPL-2.0-or-later
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class MCBParserTests(unittest.TestCase):
    def test_native_core_against_synthetic_chains(self):
        compiler = os.environ.get("CC", "cc")
        if shutil.which(compiler) is None:
            self.skipTest("host C compiler is not installed")
        with tempfile.TemporaryDirectory(prefix="m19-mcb-") as temporary:
            executable = Path(temporary) / "mcb-parser-test"
            subprocess.run(
                [compiler, "-std=c89", "-Wall", "-Wextra", "-Werror",
                 "-pedantic", "-I", str(ROOT / "tools/m19/memmap"),
                 str(ROOT / "tools/m19/memmap/mcb_parser.c"),
                 str(ROOT / "tests/m19/mcb_parser_test.c"),
                 "-o", str(executable)],
                check=True,
            )
            result = subprocess.run(
                [str(executable)], check=True, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(result.stdout.strip(), "M19 MCB parser tests passed")
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
