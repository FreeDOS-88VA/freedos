# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "confine", ROOT / "tools/m20/confine_platform_changes.py")
confine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(confine)

BASE = """int f(int x)
{
  if (x > 3)
    return 1;
  return 0;
}
"""
CHANGED = """int f(int x)
{
#if defined(PC88VA)
  x = x * 2;
#endif
  if (x >= 3)
    return 1;
  return 0;
}
"""


def view(text):
    lines = text.split("\n")
    return [l for _, l in confine.pc_view(lines)]


class ConfineTests(unittest.TestCase):
    def test_pc_view_drops_only_pc88va_branches(self):
        text = "a\n#if defined(PC88VA)\nb\n#else\nc\n#endif\n#if !defined(PC88VA)\nd\n#endif\n%ifdef WATCOM\ne\n%endif"
        self.assertEqual(view(text), ["a", "c", "d", "%ifdef WATCOM", "e", "%endif"])

    def test_unguarded_change_is_wrapped_and_baseline_restored_for_pc(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "f.c"
            path.write_text(CHANGED)
            self.assertEqual(confine.guard(path, BASE), 1)
            result = path.read_text()
            self.assertEqual(confine.norm_c(view(result)), confine.norm_c(BASE.split("\n")))
            self.assertIn("if (x >= 3)", result)  # PC-88VA keeps its change
            self.assertTrue(confine.balanced(result.split("\n")))
            # Already confined: a second pass changes nothing.
            self.assertEqual(confine.guard(path, BASE), 0)


if __name__ == "__main__":
    unittest.main()
