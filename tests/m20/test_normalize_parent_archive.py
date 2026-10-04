# SPDX-License-Identifier: GPL-2.0-or-later
"""The only allowed parent-export normalization is nonsemantic TAR metadata."""
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/m20'))
from normalize_parent_archive import normalize, records


class ParentArchiveTests(unittest.TestCase):
    def make_tar(self, path, extra=None):
        files = {'COPYING': b'license', 'LICENSE.md': b'notice',
                 'manifests/m20-components.lock.json': b'component lock',
                 'manifests/toolchains.lock.json': b'toolchain lock',
                 'tools/m20/build.sh': b'#!/bin/sh\n',
                 'tests/m20/test.py': b'check', 'config/m20/media.json': b'{}'}
        if extra:
            files.update(extra)
        with tarfile.open(path, 'w:', format=tarfile.PAX_FORMAT) as archive:
            for directory in ('config/', 'tools/', 'tests/', 'manifests/',
                              'config/m20/', 'tools/m20/', 'tests/m20/'):
                member = tarfile.TarInfo(directory)
                member.type = tarfile.DIRTYPE
                member.mode = 0o755
                archive.addfile(member)
            for name, data in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                member.mode = 0o755 if name.endswith('.sh') else 0o644
                member.uid, member.gid, member.mtime = 12, 34, 55
                archive.addfile(member, io.BytesIO(data))

    def test_only_tar_metadata_changes_and_bytes_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dst1, dst2 = (root / name for name in ('source.tar', 'one.tar', 'two.tar'))
            self.make_tar(src)
            normalize(src, dst1, 1787814827)
            normalize(src, dst2, 1787814827)
            self.assertEqual(dst1.read_bytes(), dst2.read_bytes())
            self.assertEqual(records(src), records(dst1))
            with tarfile.open(dst1) as archive:
                self.assertEqual(archive.getmember('tools/m20/build.sh').mode, 0o755)
                self.assertTrue(all(item.mtime == 1787814827 and item.uid == 0 and
                                    item.gid == 0 for item in archive.getmembers()))

    def test_unknown_path_symlink_missing_root_and_existing_output_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dst = root / 'source.tar', root / 'output.tar'
            for addition in ({'tools/unknown/private': b'bad'},
                             {'../outside': b'bad'}):
                self.make_tar(src, addition)
                with self.assertRaises(ValueError):
                    normalize(src, dst, 1787814827)
            self.make_tar(src)
            with tarfile.open(src, 'a:') as archive:
                link = tarfile.TarInfo('tools/m20/escape')
                link.type = tarfile.SYMTYPE
                link.linkname = '../secret'
                archive.addfile(link)
            with self.assertRaises(ValueError):
                normalize(src, dst, 1787814827)
            self.make_tar(src)
            normalize(src, dst, 1787814827)
            with self.assertRaises(ValueError):
                normalize(src, dst, 1787814827)


if __name__ == '__main__':
    unittest.main()
