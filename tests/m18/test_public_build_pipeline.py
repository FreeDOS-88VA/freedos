import ast
import hashlib
import inspect
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.m18 import build_image, verify_isolation, verify_source_audit

ROOT = Path(__file__).resolve().parents[2]


class PublicBuildPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.make_export()

    def tearDown(self):
        self.temp.cleanup()

    def make_export(self):
        for directory in ("tools/m18", "tests/m18", "config/m18", "manifests",
                          "components/fdkernel", "components/freecom", "components/country",
                          "components/edlin", "components/jwasm"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "tools/m18", self.root / "tools/m18", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "tests/m18", self.root / "tests/m18", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "config/m18", self.root / "config/m18", dirs_exist_ok=True)
        shutil.copyfile(ROOT / "manifests/m18-components.lock.json",
                        self.root / "manifests/m18-components.lock.json")
        shutil.copyfile(ROOT / "manifests/toolchains.lock.json",
                        self.root / "manifests/toolchains.lock.json")
        for path in (ROOT / "components/edlin", ROOT / "components/jwasm"):
            (self.root / "components" / path.name).rmdir()
            (self.root / "components" / path.name).mkdir()

    def test_allowlisted_source_tree_passes(self):
        verify_isolation.verify(self.root)
        verify_source_audit.verify(self.root)

    def test_any_historical_milestone_directory_is_rejected(self):
        for parent in ("tools", "config", "tests", "containers"):
            path = self.root / parent / "m17"
            path.mkdir(parents=True)
            with self.subTest(parent=parent), self.assertRaises(verify_isolation.IsolationError):
                verify_isolation.verify(self.root)
            path.rmdir()

    def test_suffixed_historical_milestone_directory_is_rejected(self):
        path = self.root / "tools" / "m07r2"
        path.mkdir(parents=True)
        with self.assertRaises(verify_isolation.IsolationError):
            verify_isolation.verify(self.root)

    def test_suffixless_file_reference_to_old_milestone_is_rejected(self):
        source = self.root / "tools/m18/toolchain/Dockerfile"
        source.write_text(source.read_text(encoding="ascii") +
                          "COPY tools/" + "m07r3/helper.sh /opt/\n", encoding="ascii")
        with self.assertRaises(verify_isolation.IsolationError):
            verify_isolation.verify(self.root)

    def test_source_audit_rejects_non_83_package_filename(self):
        path = self.root / "config/m18/packages.json"
        packages = json.loads(path.read_text(encoding="ascii"))
        packages["packages"][0]["files"].append("A.B.C")
        path.write_text(json.dumps(packages), encoding="ascii")
        with self.assertRaises(verify_source_audit.AuditError):
            verify_source_audit.verify(self.root)

    def test_transitive_import_and_symlink_are_rejected(self):
        source = self.root / "tools/m18/transitive.py"
        source.write_text("from tools." + "m17 import old_builder\n", encoding="ascii")
        with self.assertRaises(verify_isolation.IsolationError):
            verify_isolation.verify(self.root)
        source.unlink()
        target = self.root / "config/m18/linked.json"
        target.symlink_to(self.root / "config/m18/media.json")
        with self.assertRaises(verify_isolation.IsolationError):
            verify_isolation.verify(self.root)

    def test_source_audit_rejects_unknown_component_hash(self):
        lock_path = self.root / "manifests/m18-components.lock.json"
        lock = json.loads(lock_path.read_text(encoding="ascii"))
        lock["components"][0]["source_archive_sha256"] = "x" * 64
        lock_path.write_text(json.dumps(lock), encoding="ascii")
        with self.assertRaises(verify_source_audit.AuditError):
            verify_source_audit.verify(self.root)

    def test_fresh_empty_build_root_is_supported(self):
        root = self.root / "empty-build"
        root.mkdir()
        build_image.safe_recreate(root, ".m18-generated-root",
                                  build_image.BUILD_MARKER, "test build")
        self.assertEqual((root / ".m18-generated-root").read_text(encoding="ascii"),
                         build_image.BUILD_MARKER)

    def test_generated_build_cleanup_is_marker_guarded(self):
        root = self.root / "build/m18"
        root.mkdir(parents=True)
        marker = build_image.BUILD_MARKER
        (root / ".m18-generated-root").write_text(marker, encoding="ascii")
        self.assertEqual((root / ".m18-generated-root").read_text(), marker)
        unmarked = self.root / "build/unmarked"
        unmarked.mkdir()
        from tools.m18.clean import clean
        with self.assertRaises(ValueError):
            clean(unmarked)

    def test_pinned_source_packer_exports_all_transitive_local_imports(self):
        directory = ROOT / 'tools/m18'
        modules = {path.stem for path in directory.glob('*.py')}
        queue, seen = ['build_image'], set()
        while queue:
            name = queue.pop()
            if name in seen:
                continue
            seen.add(name)
            tree = ast.parse((directory / (name + '.py')).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module in modules:
                    queue.append(node.module)
                if isinstance(node, ast.Import):
                    queue.extend(alias.name for alias in node.names if alias.name in modules)
        exporter = inspect.getsource(build_image.build_source_bundle_pinned)
        for name in seen:
            self.assertIn('tools/m18/' + name + '.py', exporter)

    def test_fixed_source_bundle_is_deterministic_and_closed(self):
        inputs = self.root / "source-inputs"
        inputs.mkdir()
        for name in ("parent", "fdkernel", "freecom", "country", "edlin", "jwasm"):
            (inputs / (name + ".tar")).write_bytes((name + " source archive\n").encode())
        record = {
            "parent_revision": "1" * 40,
            "parent_start_sha": "2" * 40,
            "components": {},
            "source_archives_sha256": {},
            "toolchain_identity": "sha256:" + "3" * 64,
            "host_test_wheel": {},
            "source_date_epoch": 1740233872,
            "two_independent_clean_builds_equal": True,
        }
        output = self.root / "freedos-PC88VA-M18-SOURCES.tar.xz"
        first = build_image.build_source_bundle(inputs, output, record, 1740233872)
        first_bytes = output.read_bytes()
        second = build_image.build_source_bundle(inputs, output, record, 1740233872)
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, output.read_bytes())
        self.assertEqual(first["sha256"], hashlib.sha256(first_bytes).hexdigest())
        self.assertEqual(first["filename"], "freedos-PC88VA-M18-SOURCES.tar.xz")

    def test_public_output_names_match_the_pinned_packer_and_instructions(self):
        producer = inspect.getsource(build_image)
        packer = inspect.getsource(build_image.build_source_bundle_pinned)
        instructions = (ROOT / 'tools/m18/DISTRIBUTION-README.md').read_text()
        for name in ('freedos-PC88VA-M18-2HD.D88',
                     'freedos-PC88VA-M18-SOURCES.tar.xz'):
            self.assertIn(name, producer)
            self.assertIn(name, instructions)
        self.assertIn('/work/result/freedos-PC88VA-M18-SOURCES.tar.xz', packer)
        self.assertNotIn('/work/result/PC88VA-M18-SOURCES.tar.xz', packer)
        self.assertNotIn('staging_dist / "PC88VA-M18-', producer)


if __name__ == "__main__":
    unittest.main()
