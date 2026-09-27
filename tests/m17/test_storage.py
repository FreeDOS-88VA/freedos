# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import struct
import tempfile
import shutil
import json
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m17'))
from contracts import load,validate
from produce import build
from inspect_storage import inspect
from verify_source_audit import verify

class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles=load(ROOT/'config/m17/media-profiles.json')
        cls.small=cls.profiles[0]
        cls.data,cls.record=build(cls.small)

    def test_all_profiles_and_reproducibility(self):
        for p in self.profiles:
            with self.subTest(profile=p['name']):
                data,record=build(p)
                self.assertEqual(record,build(p)[1])
                result=inspect(data,p)
                self.assertEqual(result['files'],record['files'])
                self.assertEqual(result['clusters'],record['clusters'])

    def test_profile_schema_negatives(self):
        mutations=[('unknown',1),('physical_sector_bytes',2048),('logical_sector_bytes',256),
                   ('cylinders',0),('heads',True),('fat_bits',32),('sectors_per_cluster',3),
                   ('root_entries',17),('partition_start',-1),('volume_serial',2**32),
                   ('container','other'),('name','../escape')]
        for key,value in mutations:
            p=dict(self.small);p[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(p)
        for key in self.small:
            p=dict(self.small);del p[key]
            with self.subTest(missing=key),self.assertRaises(ValueError):validate(p)

    def test_truncation_and_bpb_negatives(self):
        for offset,value in [(11,1),(13,3),(14,0),(16,1),(21,0),(22,0),(28,1),(510,0)]:
            data=bytearray(self.data);data[offset]=value
            with self.subTest(offset=offset),self.assertRaises(ValueError):inspect(bytes(data),self.small)
        with self.assertRaises(ValueError):inspect(self.data[:-1],self.small)

    def test_fat_mirror_loop_orphan_and_payload(self):
        p=self.small;bps=p['logical_sector_bytes'];fatlen=self.record['fat_sectors']*bps
        for kind in ('mirror','loop','orphan','payload','crosslink','oversize'):
            data=bytearray(self.data)
            def fat12(cluster,value):
                at=bps+cluster*3//2;word=int.from_bytes(data[at:at+2],'little')
                word=(word&15|value<<4) if cluster&1 else (word&0xf000|value)
                data[at:at+2]=word.to_bytes(2,'little')
                data[bps+fatlen:bps+2*fatlen]=data[bps:bps+fatlen]
            root=bps+2*fatlen
            if kind=='mirror':data[bps+5]^=1
            if kind=='loop':fat12(2,2)
            if kind=='orphan':fat12(3,0xfff)
            if kind=='payload':data[root+p['root_entries']*32]^=1
            if kind=='crosslink':struct.pack_into('<H',data,root+64+26,2)
            if kind=='oversize':struct.pack_into('<I',data,root+32+28,0xffffffff)
            with self.subTest(kind=kind),self.assertRaises(ValueError):inspect(bytes(data),p)

    def test_partition_and_container_negatives(self):
        p=self.profiles[-1];data,_=build(p)
        for at in (8,142,148,220+446+4,220+446+8,220+446+12,220+462):
            changed=bytearray(data);changed[at]^=1
            # Offset 8 is a reserved comment, not an identity field.
            if at==8:continue
            with self.subTest(offset=at),self.assertRaises(ValueError):inspect(bytes(changed),p)

class AuditTests(unittest.TestCase):
    def test_source_binding_negatives(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            audit=json.loads((ROOT/'config/m17/source-audit.json').read_text())
            for path in ['config/m17/source-audit.json','manifests/m17-components.lock.json']+['components/fdkernel/'+p for p in audit['files']]:
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/path,target)
            verify(root)
            dest=root/'config/m17/source-audit.json'
            for mutation in ('kernel','unknown','missing','hash','content'):
                changed=json.loads(json.dumps(audit))
                if mutation=='kernel':changed['kernel_commit']='0'*40
                if mutation=='unknown':changed['files']['../other']='0'*64
                if mutation=='missing':del changed['files']['kernel/config.c']
                if mutation=='hash':changed['files']['kernel/config.c']='broken'
                if mutation=='content':changed['files']['kernel/config.c']='0'*64
                dest.write_text(json.dumps(changed))
                with self.subTest(mutation=mutation),self.assertRaises(ValueError):verify(root)

if __name__=='__main__':unittest.main()
