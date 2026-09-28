# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-side bindings for the real CONFIG.SYS/DEVICE= QA images."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ConfigQaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ROOT / 'config/m17/config-qa.json').read_text())
        cls.by_name = {profile['name']: profile for profile in cls.profiles['profiles']}

    def test_qa_profiles_are_exact_and_resolve_public_configuration_inputs(self):
        self.assertEqual(set(self.profiles), {'schema_version', 'profiles'})
        self.assertIs(type(self.profiles['schema_version']), int)
        self.assertEqual(self.profiles['schema_version'], 1)
        self.assertEqual(set(self.by_name), {
            'baseline-config', 'fdconfig-precedence', 'character-init',
            'zero-unit-init', 'loadseg-2000'})
        for profile in self.profiles['profiles']:
            self.assertEqual(set(profile), {
                'name', 'config_source', 'fdconfig_source', 'loadseg',
                'device_driver', 'expected_config_file'})
            for key in ('config_source', 'fdconfig_source'):
                source = profile[key]
                if source is not None:
                    path = ROOT / 'config/m17' / source
                    self.assertEqual(path.parent, ROOT / 'config/m17')
                    self.assertTrue(path.is_file())
            config = (ROOT / 'config/m17' / profile['config_source']).read_text()
            match = re.search(r'^PC88VA_LOADSEG=([0-9A-Fa-f]+)h?\s*$',
                              config, flags=re.MULTILINE)
            self.assertIsNotNone(match)
            self.assertEqual(match.group(1).upper(), profile['loadseg'])
            self.assertEqual(profile['expected_config_file'],
                             'FDCONFIG.SYS' if profile['fdconfig_source'] else 'CONFIG.SYS')

    def test_fdconfig_precedence_and_device_directives_are_distinguishing(self):
        default = (ROOT / 'config/m17/CONFIG.SYS').read_text()
        selected = (ROOT / 'config/m17/FDCONFIG.control').read_text()
        self.assertIn('BUFFERS=10', default)
        self.assertIn('FILES=16', default)
        self.assertIn('BUFFERS=8', selected)
        self.assertIn('FILES=12', selected)
        self.assertEqual(self.by_name['fdconfig-precedence']['expected_config_file'],
                         'FDCONFIG.SYS')
        for name, driver in (('character-init', 'CFGDEV.SYS'),
                             ('zero-unit-init', 'CFGNONE.SYS')):
            fdconfig = (ROOT / 'config/m17' /
                        self.by_name[name]['fdconfig_source']).read_text()
            directives = [line.split('=', 1)[1].strip()
                          for line in fdconfig.splitlines()
                          if line.upper().startswith('DEVICE=')]
            self.assertEqual(directives, [driver])
            self.assertEqual(self.by_name[name]['device_driver'], driver)
            self.assertNotIn('SCSI', driver)

    def test_qa_driver_sources_have_positive_and_zero_unit_init_shapes(self):
        driver = (ROOT / 'tests/m17/config_device.asm').read_text()
        self.assertIn('dw 0x8000', driver)
        self.assertIn('mov word [es:bx+14], resident_end', driver)
        self.assertIn('mov byte [es:bx+13],0', driver)
        self.assertIn('M17-DEVICE-INIT', driver)
        self.assertIn('M17-DEVICE-DECLINED', driver)
        probe = (ROOT / 'tests/m17/config_probe.asm').read_text()
        self.assertIn("device: db 'VA17TEST',0", probe)
        state = (ROOT / 'tests/m17/config_state.asm').read_text()
        for field in ('BUFFERS=', ' LAST=', ' FILES=', ' UNITS=', ' MAXFREE_PARAS='):
            self.assertIn(field, state)
        memory = (ROOT / 'tests/m17/config_memory.asm').read_text()
        self.assertIn('mov ax,0x4800', memory)
        self.assertIn('MAXFREE_PARAS=', memory)

    def test_kernel_source_audit_keeps_config_loader_and_registration_claims_bound(self):
        config = (ROOT / 'components/fdkernel/kernel/config.c').read_text()
        main = (ROOT / 'components/fdkernel/kernel/main.c').read_text()
        device = (ROOT / 'components/fdkernel/hdr/device.h').read_text()
        self.assertLess(config.index('open("fdconfig.sys"'),
                        config.index('open("config.sys"'))
        self.assertIn('{"DEVICE", 2, Device}', config)
        self.assertLess(main.index('DoConfig(0);'), main.index('DoConfig(1);'))
        self.assertLess(main.index('DoConfig(1);'), main.index('DoConfig(2);'))
        self.assertIn('rq.r_firstunit = LoL->nblkdev;', main)
        self.assertIn('dhp->dh_name[0] = rq.r_nunits;', main)
        self.assertIn('dpb->dpb_unit = LoL->nblkdev;', main)
        self.assertIn('#define failure(x)', device)
        # Preserve, do not silently patch, the inherited VA INIT status predicate.
        self.assertIn('(rq.r_status & (S_ERROR | S_DONE)) == S_ERROR', main)


if __name__ == '__main__':
    unittest.main()
