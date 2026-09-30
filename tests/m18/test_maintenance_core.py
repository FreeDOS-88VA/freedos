# SPDX-License-Identifier: GPL-2.0-or-later
"""Compile and execute the production FAT12/BPB validation core on host fixtures."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class MaintenanceCoreTests(unittest.TestCase):
    def compile_and_run(self, name, sources, include_dirs, stdin=None):
        compiler = shlex.split(os.environ.get("CC", "cc"))
        with tempfile.TemporaryDirectory(prefix="m18-{}-".format(name)) as temporary:
            executable = Path(temporary) / name
            command = compiler + ["-std=c89", "-Wall", "-Wextra", "-Werror"]
            command.extend("-I" + str(path) for path in include_dirs)
            command.extend(str(ROOT / source) for source in sources)
            command.extend(["-o", str(executable)])
            subprocess.run(command, check=True)
            return subprocess.run(
                [str(executable)], check=True, capture_output=True, text=True,
                input=stdin,
            ).stdout

    def test_dos_absolute_disk_adapter_matches_large_model_far_abi(self):
        header = (ROOT / "tools/m18/maintenance/volume.h").read_text(encoding="ascii")
        adapter = (ROOT / "tools/m18/maintenance/diskio.asm").read_text(encoding="ascii")
        self.assertIn("unsigned __far __cdecl m18_abs_sector", header)
        self.assertIn("unsigned sector, void __far *buffer", header)
        self.assertIn("global _m18_abs_sector, m18_critical_", adapter)
        self.assertIn("mov bx, [bp+12]", adapter)
        self.assertIn("mov si, [bp+14]", adapter)
        self.assertIn("m18_critical_:", adapter)
        self.assertIn("retf", adapter)

    def test_native_profile_and_fat_chain_fixtures(self):
        output = self.compile_and_run(
            "fat12-test",
            ["tools/m18/maintenance/fat12.c", "tests/m18/fat12_test.c"],
            [ROOT / "tools/m18/maintenance"],
        )
        self.assertIn("M18 FAT12 native-profile tests: PASS", output)

    def test_native_volume_scanner_on_read_only_sector_fixtures(self):
        output = self.compile_and_run(
            "volume-test",
            ["tools/m18/maintenance/fat12.c", "tools/m18/maintenance/volume.c",
             "tests/m18/volume_test.c"],
            [ROOT / "tests/m18/stubs", ROOT / "tools/m18/maintenance"],
        )
        self.assertIn("M18 native-volume synthetic read-only tests: PASS", output)

    def test_sys_installs_boot_only_on_the_source_loader_extent(self):
        # Two transfers reach the confirmation prompt; the refused cases do not.
        output = self.compile_and_run(
            "sys-test",
            ["tools/m18/maintenance/fat12.c", "tools/m18/maintenance/volume.c",
             "tests/m18/sys_test.c"],
            [ROOT / "tests/m18/stubs", ROOT / "tools/m18/maintenance"],
            stdin="SYS\nSYS\n",
        )
        self.assertIn("M18 SYS loader-extent transfer tests: PASS", output)


if __name__ == "__main__":
    unittest.main()
