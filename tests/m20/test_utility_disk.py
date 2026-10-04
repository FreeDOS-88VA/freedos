# SPDX-License-Identifier: GPL-2.0-or-later
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/m20"))
from compose_image import compose_data, data_disk_spec
from media import inspect
from component_set import CORE, locked_names


class UtilityDiskTests(unittest.TestCase):
    def test_data_disk_reads_back_and_is_not_a_boot_loader_disk(self):
        payloads = {"FIND.EXE": b"MZ" + bytes(3000), "README.TXT": b"hello\r\n",
                    "COPYING": b"x" * 2049}
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            image = compose_data(payloads, out, 1791023315, "FDOS-PC88VA-UTIL", "M20-UTIL")
            report, files = inspect(image, data_disk_spec("FDOS-PC88VA-UTIL", "M20-UTIL"))
            self.assertEqual(files, payloads)
            self.assertTrue(report["fat_copies_equal"])
            self.assertNotIn("LOADER.BIN", files)
            with self.assertRaises(ValueError):
                compose_data({"BIG.BIN": bytes(2 * 1024 * 1024)}, out, 1, "X", "Y", stem="big")

    def test_configuration_names_pinned_components_and_dos_names(self):
        config = json.loads((ROOT / "config/m20/utility-disk.json").read_text())
        names = set(locked_names())
        self.assertTrue(set(CORE) <= names)
        for package in config["packages"]:
            self.assertTrue(set(package["source_locks"]) <= names)
            for filename in package["files"]:
                self.assertRegex(filename, r"^[A-Z0-9_-]{1,8}\.[A-Z0-9]{1,3}$")
        for relative in config["notices"].values():
            self.assertTrue((ROOT / relative).is_file())
        self.assertTrue((ROOT / config["readme"]).read_bytes().isascii())

    @unittest.skipUnless(shutil.which("git") and (ROOT / "components/find/.git").exists(),
                         "host-only: requires the find checkout and git")
    def test_library_pins_equal_finds_own_submodule_commits(self):
        lock = {item["name"]: item["commit"] for item in
                json.loads((ROOT / "manifests/m20-components.lock.json").read_text())["components"]}
        for library in ("kitten", "tnyprntf"):
            entry = subprocess.run(["git", "-C", str(ROOT / "components/find"), "ls-tree",
                                    lock["find"], library], check=True, capture_output=True,
                                   text=True).stdout.split()
            self.assertEqual(entry[1], "commit")
            self.assertEqual(entry[2], lock[library])


if __name__ == "__main__":
    unittest.main()
