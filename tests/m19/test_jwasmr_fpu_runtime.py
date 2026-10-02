# SPDX-License-Identifier: GPL-2.0-or-later
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.m19.assembler.build_jwasmr import (
    X87ID_ENTRY, X87ID_SOURCE, verify_floating_runtime, verify_no_wait_probe)


class JwasmrFpuRuntimeTests(unittest.TestCase):
    MAP = "\n".join([
        'Module: /opt/openwatcom-1.9/lib286/math87l.lib(strtod.c)',
        'Module: /opt/openwatcom-1.9/lib286/dos/emu87.lib(initemu.asm)',
        'Module: /opt/openwatcom-1.9/lib286/dos/emu87.lib(emu8087.asm)',
        'Module: /opt/openwatcom-1.9/lib286/dos/emu87.lib(dosinit.asm)',
    ])

    def test_both_conversion_and_full_emulation_are_required(self):
        verify_floating_runtime(self.MAP)
        for module in ('strtod.c', 'initemu.asm', 'emu8087.asm', 'dosinit.asm'):
            with self.subTest(module=module), self.assertRaisesRegex(ValueError, 'software 8087'):
                verify_floating_runtime(self.MAP.replace(module, 'missing.module'))
        with self.assertRaisesRegex(ValueError, 'software 8087'):
            verify_floating_runtime(self.MAP + '\n' + self.MAP)
        with self.assertRaisesRegex(ValueError, 'software 8087'):
            verify_floating_runtime(self.MAP + '\nModule: /opt/lib286/dos/noemu87.lib(fake)')


class NoWaitProbeTests(unittest.TestCase):
    MAP = "\n".join([
        "Module: /tmp/out/objects/x87id.obj(/tmp/tools/m19/assembler/x87id.asm)",
        "0000:0010      __x87id",
    ])

    def image(self, entry=X87ID_ENTRY):
        return bytes(0x10) + entry + bytes(16)

    def test_project_probe_is_required_at_the_mapped_address(self):
        self.assertEqual(verify_no_wait_probe(self.MAP, self.image()), 0x10)
        with self.assertRaisesRegex(ValueError, "no-WAIT"):
            verify_no_wait_probe(self.MAP + "\nModule: /opt/lib286/dos/clibl.lib(init8087)",
                                 self.image())
        with self.assertRaisesRegex(ValueError, "no-WAIT"):
            verify_no_wait_probe(self.MAP.replace("x87id.obj", "other.obj"), self.image())
        with self.assertRaisesRegex(ValueError, "lacks"):
            verify_no_wait_probe(self.MAP.replace("__x87id", "__other"), self.image())
        library_entry = bytes.fromhex("558bec2bc0509bdbe3")
        with self.assertRaisesRegex(ValueError, "does not start"):
            verify_no_wait_probe(self.MAP, self.image(library_entry))

    @unittest.skipIf(shutil.which("nasm") is None, "nasm is required")
    def test_no_wait_instruction_precedes_the_coprocessor_answer(self):
        source = X87ID_SOURCE.read_text(encoding="ascii")
        flat = "\n".join(line for line in source.splitlines()
                          if not line.startswith(("segment", "global", "extern")))
        flat = flat.replace("call __init_8087_", "call 0")
        with tempfile.TemporaryDirectory() as temporary:
            asm = Path(temporary) / "x87id.asm"
            binary = Path(temporary) / "x87id.bin"
            asm.write_text(flat, encoding="ascii")
            subprocess.run(["nasm", "-f", "bin", "-o", str(binary), str(asm)], check=True)
            code = binary.read_bytes()
        entry = code.index(X87ID_ENTRY)
        decision = code.index(bytes.fromhex("80fc03"), entry)  # cmp ah,3
        self.assertNotIn(0x9B, code[entry:decision])
        self.assertIn(bytes.fromhex("dbe3"), code[entry:decision])      # FNINIT
        self.assertIn(bytes.fromhex("d97efc"), code[entry:decision])    # FNSTCW


if __name__ == '__main__':
    unittest.main()
