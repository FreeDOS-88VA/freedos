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
        for notice in config["notices"].values():
            relative = notice if isinstance(notice, str) else notice["source"]
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

    @unittest.skipUnless(shutil.which("git") and (ROOT / "components/choice/.git").exists(),
                         "host-only: requires component checkouts and git")
    def test_fork_bases_are_freedos_14_cutoff_commits_and_ancestors(self):
        forks = [item for item in json.loads(
            (ROOT / "manifests/m20-components.lock.json").read_text())["components"]
            if item.get("selection", "").startswith("project fork; upstream base is")]
        self.assertTrue(forks)
        for item in forks:
            path = ROOT / item["path"]
            upstream = subprocess.run(["git", "-C", str(path), "rev-parse", "--verify", "-q",
                                       "upstream/master"], capture_output=True, text=True)
            if upstream.returncode:
                self.skipTest("upstream is not fetched: " + item["name"])
            expected = subprocess.run(["git", "-C", str(path), "rev-list", "-1",
                                       "--before=2025-04-10T00:00:00", upstream.stdout.strip()],
                                      check=True, capture_output=True, text=True).stdout.strip()
            with self.subTest(component=item["name"]):
                self.assertTrue(item["repository"].startswith("https://github.com/nakatamaho/"))
                self.assertTrue(item["upstream_repository"].startswith("https://github.com/FDOS/"))
                self.assertEqual(item["upstream_base_commit"], expected)
                subprocess.run(["git", "-C", str(path), "merge-base", "--is-ancestor",
                                expected, item["commit"]], check=True)


    def test_extracted_license_block_is_complete(self):
        from finish_image import notice_payload
        config = json.loads((ROOT / "config/m20/utility-disk.json").read_text())
        text = notice_payload(config["notices"]["COMP.LIC"]).decode("ascii")
        self.assertTrue(text.startswith("Copyright (c) 2003  Paul Vojta\r\n"))
        self.assertIn("Permission is hereby granted", text)
        self.assertIn("shall be included", text)
        self.assertTrue(text.endswith("THE USE OR OTHER DEALINGS IN THE SOFTWARE.\r\n"))
        with self.assertRaises(ValueError):
            notice_payload(dict(config["notices"]["COMP.LIC"], through="NOT PRESENT"))


if __name__ == "__main__":
    unittest.main()
