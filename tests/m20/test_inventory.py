# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("inventory", ROOT / "tools/m20/inventory.py")
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def commit(repo, path, text, message):
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(text)
    git(repo, "add", path)
    git(repo, "commit", "-q", "-m", message)
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True).stdout.strip()


class InventoryTests(unittest.TestCase):
    def test_areas_and_classes(self):
        self.assertEqual(inventory.area("pc88va/kernel/startup.asm"), "pc88va")
        self.assertEqual(inventory.area("sys/pc88va.c"), "pc88va")
        self.assertEqual(inventory.area("nec98/kernel/kernel.asm"), "pc98")
        self.assertEqual(inventory.area("ibmpc/makefile"), "platform")
        self.assertEqual(inventory.area("kernel/config.c"), "shared")
        self.assertEqual(inventory.classify({"pc88va"}, False), "pc88va-only")
        self.assertEqual(inventory.classify({"pc98", "meta"}, False), "pc98-only")
        self.assertEqual(inventory.classify({"platform", "pc98"}, False), "platform-scaffolding")
        self.assertEqual(inventory.classify({"pc88va", "shared"}, False), "touches-shared")
        self.assertEqual(inventory.classify({"meta"}, False), "meta-only")
        # An official upstream change is reported as such regardless of paths.
        self.assertEqual(inventory.classify({"shared"}, True), "upstream-backport")

    def test_actual_history_patch_id_markers_and_sjis(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Test")
            base = commit(repo, "kernel/a.c", b"int a;\n", "base")
            git(repo, "branch", "official")
            git(repo, "switch", "-q", "official")
            commit(repo, "kernel/fix.c", b"int fix;\n", "official fix")
            git(repo, "switch", "-q", "main")
            # The same change re-applied with a different commit identity.
            commit(repo, "kernel/fix.c", b"int fix;\n", "backported fix")
            commit(repo, "pc88va/b.asm", b"%ifdef PC88VA\n%endif\n", "va adapter")
            commit(repo, "kernel/c.c", b"#ifdef DBCS\n/* \x82\xa0 */\n#endif\n", "sjis")
            rows = inventory.inventory(repo, base, "main", "official")
            self.assertEqual([r["class"] for r in rows],
                             ["upstream-backport", "pc88va-only", "touches-shared"])
            self.assertIsNotNone(rows[0]["upstream_commit"])
            self.assertEqual(rows[1]["markers"], {"PC88VA": 1})
            self.assertEqual(rows[2]["markers"], {"DBCS": 1})
            self.assertIn("| sjis |", inventory.markdown(rows))


if __name__ == "__main__":
    unittest.main()
