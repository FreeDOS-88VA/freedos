import json
from pathlib import Path
import tempfile
import unittest

from tools.m20.compose_image import compose
from tools.m20.media import derive_layout, inspect

ROOT = Path(__file__).resolve().parents[2]


class Native2HDMediaTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((ROOT / "config/m20/loader.json").read_text(encoding="ascii"))
        self.spec = json.loads((ROOT / "config/m20/media.json").read_text(encoding="ascii"))

    def test_declared_profile_recomputes_native_2hd_fat12_geometry(self):
        layout = derive_layout(self.spec)
        for name, expected in {
            "bytes_per_sector": 1024, "cylinders": 80, "heads": 2,
            "sectors_per_track": 8, "physical_sector_id_base": 1,
            "total_bytes": 1310720, "total_sectors": 1280,
        }.items():
            self.assertEqual(self.spec["geometry"][name], expected)
        self.assertEqual(self.spec["filesystem"]["fat_type"], "FAT12")
        self.assertEqual(layout["total_bytes"], 1310720)
        self.assertEqual(layout["data_clusters"], 1269)
        self.assertGreaterEqual(self.spec["filesystem"]["sectors_per_fat"] * 1024,
                                layout["fat_bytes_required"])

    def test_native_d88_roundtrips_exact_root_files_and_cluster_accounting(self):
        payloads = {
            "LOADER.BIN": bytes((index * 7) & 0xff for index in range(1536)),
            "CONFIG.SYS": b"PC88VA_LOADSEG=1000\r\nSET PATH=A:\\\r\n",
            "HELLO.ASM": b"bits 16\r\norg 100h\r\nret\r\n",
            "JWASM.LIC": b"Public test license payload\r\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            compose(payloads, self.profile, output, 1787814827)
            image = (output / "media.d88").read_bytes()
            report, files = inspect(image, self.spec)
            self.assertEqual(files, payloads)
            self.assertTrue(report["fat_copies_equal"])
            self.assertEqual(report["volume_label"], "PC88VA-M20")
            self.assertGreater(len(report["free_clusters"]), 1200)
            self.assertEqual((output / "media.json").is_file(), True)

    def test_d88_readback_rejects_changed_sector_and_trailing_bytes(self):
        payloads = {
            "LOADER.BIN": b"L" * 1024,
            "CONFIG.SYS": b"FILES=16\r\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            compose(payloads, self.profile, output, 1787814827)
            image = bytearray((output / "media.d88").read_bytes())
            with self.assertRaises((ValueError, RuntimeError)):
                inspect(bytes(image) + b"trailing", self.spec)
            bpb_offset = self.spec["d88"]["header_size"] + self.spec["d88"]["sector_header_size"] + 11
            image[bpb_offset] ^= 1
            with self.assertRaises((ValueError, RuntimeError)):
                inspect(bytes(image), self.spec)

    def test_one_directory_level_reads_back(self):
        payloads = {
            "LOADER.BIN": b"L" * 1024,
            "CONFIG.SYS": b"FILES=16\r\n",
            "MSDOS/COMMAND.COM": bytes(range(256)) * 9,
            "MSDOS/README.TXT": b"x\r\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            compose(payloads, self.profile, output, 1787814827)
            report, files = inspect((output / "media.d88").read_bytes(), self.spec)
            self.assertEqual(files, payloads)
            self.assertEqual(set(report["directories"]), {"MSDOS"})
            with self.assertRaises(ValueError):
                compose({"LOADER.BIN": b"L", "A/B/C.TXT": b"x"}, self.profile,
                        output / "deep", 1787814827)

    def test_native_root_capacity_is_enforced(self):
        payloads = {"LOADER.BIN": b"L" * 1024}
        payloads.update({"F{:07d}.TXT".format(index): b"x"
                        for index in range(self.spec["filesystem"]["root_entries"])})
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises((KeyError, ValueError)):
                compose(payloads, self.profile, Path(temporary), 1787814827)


if __name__ == "__main__":
    unittest.main()
