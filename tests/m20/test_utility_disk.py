# SPDX-License-Identifier: GPL-2.0-or-later
import hashlib
import json
import re
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
        from data_disks import DATA_DISKS
        for kind, entry in DATA_DISKS.items():
            with self.subTest(disk=kind):
                self.check_configuration(json.loads((ROOT / entry["config"]).read_text()))

    def test_data_disks_have_distinct_names_and_programs(self):
        from data_disks import DATA_DISKS
        configs = [json.loads((ROOT / entry["config"]).read_text()) for entry in DATA_DISKS.values()]
        for key in ("filename", "d88_disk_name", "volume_label"):
            values = [config["disk"][key] for config in configs]
            self.assertEqual(len(values), len(set(values)), key)
        programs = [package["id"] for config in configs for package in config["packages"]]
        self.assertEqual(len(programs), len(set(programs)))

    def check_configuration(self, config):
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
                self.assertTrue(item["repository"].startswith("https://github.com/FreeDOS-88VA/"))
                if not item["upstream_repository"].startswith("https://github.com/FDOS/"):
                    # Only with a stated reason (DEBUG: FDOS/debug is obsolete).
                    self.assertGreater(len(item.get("upstream_reason", "")), 40)
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


    @unittest.skipUnless(shutil.which("git") and (ROOT / "components/fc/.git").exists(),
                         "host-only: requires component checkouts and git")
    def test_baseline_exemptions_are_explained_and_narrow(self):
        lock = json.loads((ROOT / "manifests/m20-components.lock.json").read_text())
        exempt = {item["name"]: item for item in lock["components"] if item.get("baseline_exemption")}
        self.assertEqual(set(exempt), {"fc", "attrib", "tree", "replace", "exe2bin",
                                       "unzip", "zip", "gzip"})
        for name, item in exempt.items():
            with self.subTest(component=name):
                self.assertGreater(len(item["baseline_exemption"]), 80)
                check = item["baseline_check"]
                if check == "lfn-failure-tests-only":
                    self.check_lfn_failure_only(item)
                elif check == "platform-branches-only":
                    self.check_platform_branches_only(item)
                elif check == "unmodified-import":
                    self.check_unmodified_import(item)
                else:
                    self.fail("unknown baseline check: " + check)

    @unittest.skipUnless(shutil.which("git") and (ROOT / "components/replace/.git").exists(),
                         "host-only: requires component checkouts and git")
    def test_package_imports_match_their_provenance_record(self):
        lock = json.loads((ROOT / "manifests/m20-components.lock.json").read_text())
        imports = [item for item in lock["components"] if item.get("upstream_package")]
        self.assertEqual({item["name"] for item in imports},
                         {"replace", "exe2bin", "unzip", "zip", "gzip"})
        for item in imports:
            path, package = ROOT / item["path"], item["upstream_package"]
            git = lambda *args: subprocess.run(["git", "-C", str(path), *args], check=True,
                                               capture_output=True).stdout
            with self.subTest(component=item["name"]):
                self.assertEqual(git("rev-list", "--max-parents=0", item["commit"]).decode().split(),
                                 [package["import_commit"]])
                subprocess.run(["git", "-C", str(path), "merge-base", "--is-ancestor",
                                item["upstream_base_commit"], item["commit"]], check=True)
                provenance = git("show", item["upstream_base_commit"] + ":PROVENANCE.md").decode()
                self.assertIn(package["url"], provenance)
                self.assertIn(package["zip_sha256"], provenance)
                rows = re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", provenance, re.M)
                # Members of an inner SOURCES.ZIP are committed beside it.
                committed = [(str(Path(name.split("!")[0]).parent / name.split("!")[1])
                              if "!" in name else name, digest)
                             for name, digest in rows if "not committed" not in name]
                imported = git("ls-tree", "-r", "--name-only", package["import_commit"]).decode().split()
                self.assertEqual(sorted(name for name, _ in committed), sorted(imported))
                for name, digest in committed:
                    data = git("show", package["import_commit"] + ":" + name)
                    self.assertEqual(hashlib.sha256(data).hexdigest(), digest, name)

    def test_host_jwasm_is_locked_from_the_pinned_jwasm_component(self):
        from utilities.build_tools import TOOLS, derived_tool
        lock = {item["name"]: item for item in
                json.loads((ROOT / "manifests/m20-components.lock.json").read_text())["components"]}
        record = derived_tool("jwasm")
        self.assertEqual(record["source_commit"], lock[record["source_component"]]["commit"])
        self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
        users = [name for name, spec in TOOLS.items() if spec["kind"] == "jwasm"]
        self.assertEqual(users, ["debug"])
        for name in users:
            self.assertEqual(TOOLS[name]["host_components"], ["jwasm"])
            self.assertNotIn("baseline_exemption", lock[name])

    def test_upstream_view_drops_only_platform_branches(self):
        fork = ["a", "#ifdef __WATCOMC__", "w", "#else", "b", "#endif",
                "#if defined X", "x", "#elif defined __WATCOMC__", "w2", "#else", "y", "#endif",
                "#ifdef PC88VA", "va", "#else", "pc", "#endif", "#ifndef PC88VA", "pc2", "#endif",
                "#ifdef OTHER", "o", "#endif"]
        self.assertEqual(upstream_view(fork),
                         ["a", "b", "#if defined X", "x", "#else", "y", "#endif",
                          "pc", "pc2", "#ifdef OTHER", "o", "#endif"])

    def check_unmodified_import(self, item):
        """The pinned source is the package import plus its provenance record."""
        path, package = ROOT / item["path"], item["upstream_package"]
        self.assertEqual(item["commit"], item["upstream_base_commit"])
        status = subprocess.run(["git", "-C", str(path), "diff", "--name-status",
                                 package["import_commit"], item["commit"]],
                                check=True, capture_output=True, text=True).stdout.split("\n")
        self.assertEqual([line for line in status if line], ["A\tPROVENANCE.md"])

    def check_lfn_failure_only(self, item):
        diff = subprocess.run(["git", "-C", str(ROOT / item["path"]), "diff", "-U0",
                               item["upstream_base_commit"], item["commit"]],
                              check=True, capture_output=True, text=True,
                              errors="replace").stdout
        changed = [line for line in diff.splitlines()
                   if line[:1] in "+-" and not line.startswith(("+++", "---"))]
        self.assertTrue(changed)
        comment = False
        for line in changed:
            body = line[1:].strip()
            if body.startswith("/*"):
                comment = True
            allowed = (comment or not body or "r.x.cflag" in body or "LFN_FAILED" in body)
            if body.endswith("*/"):
                comment = False
            self.assertTrue(allowed, line)

    def check_platform_branches_only(self, item):
        """Dropping __WATCOMC__ and PC88VA branches must give the upstream files back.

        New files are allowed only in an Open Watcom-only directory.
        """
        path = ROOT / item["path"]
        status = subprocess.run(["git", "-C", str(path), "diff", "--name-status",
                                 item["upstream_base_commit"], item["commit"]],
                                check=True, capture_output=True, text=True).stdout.split("\n")
        changed = [line.split("\t") for line in status if line]
        self.assertTrue(changed)
        for kind, name in changed:
            if kind == "A":
                self.assertIn("/watcom/", "/" + name, name)
                continue
            self.assertEqual(kind, "M", name)

            def show(rev):
                return subprocess.run(["git", "-C", str(path), "show", rev + ":" + name],
                                      check=True, capture_output=True).stdout.decode("latin-1")
            base = show(item["upstream_base_commit"]).replace("\r\n", "\n").split("\n")
            out = upstream_view(show(item["commit"]).replace("\r\n", "\n").split("\n"))
            # Whitespace around a preprocessor '#' does not change the source.
            normalize = lambda lines: [re.sub(r"^#\s+", "#", l.strip()) for l in lines]
            self.assertEqual(normalize(out), normalize(base), name)


PLATFORM = r"(__WATCOMC__|PC88VA)"


def upstream_view(lines):
    """Lines of a fork file with __WATCOMC__ and PC88VA undefined, keeping
    every other preprocessor directive (the upstream view)."""
    out, stack = [], []   # entries: [kind, keep] kind: known/added-elif/other
    for line in lines:
        word = re.sub(r"^#\s+", "#", line.strip())
        keep = all(entry[1] for entry in stack)
        if re.match(r"#ifdef\s+" + PLATFORM + r"\b", word):
            stack.append(["known", False]); continue
        if re.match(r"#ifndef\s+" + PLATFORM + r"\b", word):
            stack.append(["known", True]); continue
        if word.startswith("#if"):
            stack.append(["other", True])
            if keep: out.append(line)
            continue
        if re.match(r"#elif\s+defined\s*\(?\s*" + PLATFORM + r"\b", word) and stack \
                and stack[-1][0] == "other":
            stack[-1] = ["added-elif", False]; continue
        if word.startswith("#else") and stack:
            entry = stack[-1]
            if entry[0] == "known":
                entry[1] = not entry[1]; continue
            if entry[0] == "added-elif":
                stack[-1] = ["other", True]
            if all(e[1] for e in stack[:-1]): out.append(line)
            continue
        if word.startswith("#endif") and stack:
            entry = stack.pop()
            if entry[0] != "known" and all(e[1] for e in stack): out.append(line)
            continue
        if keep:
            out.append(line)
    return out

if __name__ == "__main__":
    unittest.main()
