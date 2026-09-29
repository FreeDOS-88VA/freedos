# SPDX-License-Identifier: GPL-2.0-or-later
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
from unicorn.x86_const import (
    UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CS, UC_X86_REG_DS,
    UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_DX, UC_X86_REG_EFLAGS,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m18'))
import build_allocator_qa as qa


class AllocatorQaTests(unittest.TestCase):
    def test_probe_initial_resize_failure_cannot_print_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ALLOC.COM'
            subprocess.run(['nasm', '-f', 'bin',
                            str(ROOT / 'tools/m18/qa/alloc.asm'), '-o', str(path)],
                           check=True)
            data = path.read_bytes()
        self.assertLess(len(data), 4096)
        uc = Uc(UC_ARCH_X86, UC_MODE_16)
        uc.mem_map(0, 0x100000)
        uc.mem_write(0x10100, data)
        for register in (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS):
            uc.reg_write(register, 0x1000)
        output = bytearray()
        exit_codes = []
        resized = []

        def interrupt(machine, number, _):
            self.assertEqual(number, 0x21)
            ax = machine.reg_read(UC_X86_REG_AX)
            ah = ax >> 8
            if ah == 0x4a:
                resized.append(machine.reg_read(UC_X86_REG_BX))
                self.assertEqual(resized[-1], (len(data) + 256 + 15) // 16)
                machine.reg_write(UC_X86_REG_AX, 8)
                machine.reg_write(UC_X86_REG_EFLAGS,
                                  machine.reg_read(UC_X86_REG_EFLAGS) | 1)
            elif ah == 9:
                address = machine.reg_read(UC_X86_REG_DS) * 16 + machine.reg_read(UC_X86_REG_DX)
                for offset in range(200):
                    value = machine.mem_read(address + offset, 1)[0]
                    if value == ord('$'):
                        break
                    output.append(value)
                else:
                    self.fail('unbounded DOS string')
            elif ah == 2:
                output.append(machine.reg_read(UC_X86_REG_DX) & 255)
            elif ah == 0x4c:
                exit_codes.append(ax & 255)
                machine.emu_stop()
            else:
                self.fail('unexpected DOS call before resize succeeded')

        uc.hook_add(UC_HOOK_INTR, interrupt)
        uc.emu_start(0x10100, 0xfffff, count=1000)
        self.assertEqual(len(resized), 1)
        self.assertEqual(exit_codes, [1])
        self.assertEqual(output, b'ALLOC: FAIL stage 01\r\n')

    def test_qa_rejects_stale_sources_and_payload_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'inputs').mkdir()
            archive = b'original synthetic source archive'
            (root / 'inputs/parent.tar').write_bytes(archive)
            revisions = {'parent': '1' * 40}
            manifest = {'parent_revision': '1' * 40,
                        'component_revisions': revisions,
                        'source_archives_sha256': {'parent': qa.digest(archive)},
                        'two_independent_clean_builds_equal': True}
            for run in ('run-1', 'run-2'):
                path = root / run
                path.mkdir()
                records = {}
                for name in qa.PROGRAMS:
                    payload = name.encode('ascii')
                    (path / name).write_bytes(payload)
                    records[name] = {'size_bytes': len(payload), 'sha256': qa.digest(payload)}
                (path / 'artifacts.json').write_text(json.dumps(records))
            self.assertEqual(set(qa.verified_payloads(root, manifest, revisions)), set(qa.PROGRAMS))
            with self.assertRaisesRegex(ValueError, 'current pins'):
                qa.verified_payloads(root, manifest, {'parent': '2' * 40})
            manifest['source_archives_sha256']['unknown'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'references'):
                qa.verified_payloads(root, manifest, revisions)
            del manifest['source_archives_sha256']['unknown']
            (root / 'inputs/parent.tar').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'archive drift'):
                qa.verified_payloads(root, manifest, revisions)
            (root / 'inputs/parent.tar').write_bytes(archive)
            (root / 'run-2/MEMMAP.EXE').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'artifact drift'):
                qa.verified_payloads(root, manifest, revisions)


if __name__ == '__main__':
    unittest.main()
