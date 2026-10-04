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
                         "host-only: requires component checkouts and git")
    def test_library_pins_equal_each_programs_own_submodule_commits(self):
        from utilities.build_tools import TOOLS
        lock = {item["name"]: item["commit"] for item in
                json.loads((ROOT / "manifests/m20-components.lock.json").read_text())["components"]}
        checked = 0
        for name, spec in TOOLS.items():
            if not spec.get("kitten"):
                continue
            for library, component in (("kitten", spec["kitten"]), ("tnyprntf", "tnyprntf")):
                entry = subprocess.run(["git", "-C", str(ROOT / "components" / name), "ls-tree",
                                        lock[name], library], check=True, capture_output=True,
                                       text=True).stdout.split()
                with self.subTest(program=name, library=library):
                    self.assertEqual(entry[1], "commit")
                    self.assertEqual(entry[2], lock[component])
                checked += 1
        self.assertGreater(checked, 0)

    @unittest.skipUnless(shutil.which("git") and (ROOT / "components/sort/.git").exists(),
                         "host-only: requires component checkouts and git")
    def test_release_cutoff_selection_is_the_last_commit_before_freedos_14(self):
        rule = "last upstream commit on or before the FreeDOS 1.4 release (2025-04-09)"
        items = [item for item in json.loads(
            (ROOT / "manifests/m20-components.lock.json").read_text())["components"]
            if item.get("selection") == rule]
        self.assertTrue(items)
        for item in items:
            path = ROOT / item["path"]
            branch = subprocess.run(["git", "-C", str(path), "rev-parse", "--verify", "-q",
                                     "origin/" + item["branch"]], capture_output=True, text=True)
            if branch.returncode:
                self.skipTest("upstream branch is not fetched: " + item["name"])
            expected = subprocess.run(["git", "-C", str(path), "rev-list", "-1",
                                       "--before=2025-04-10T00:00:00", branch.stdout.strip()],
                                      check=True, capture_output=True, text=True).stdout.strip()
            with self.subTest(component=item["name"]):
                self.assertEqual(item["commit"], expected)


if __name__ == "__main__":
    unittest.main()
