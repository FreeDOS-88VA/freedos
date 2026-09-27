#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""M16-owned FAT12/D88 primitives; no historical milestone runtime imports.

Maintained copy of the parent-owned M15 implementation at parent revision
1af9974700cd4dd1164cc0df56cc062925376148. This copy carries only the pure
FAT12/D88 algorithms needed by M16, with M16-specific media profiles and tests.
"""
from __future__ import annotations
import hashlib
import re
import struct
from datetime import datetime, timezone

DOS_NAME_RE = re.compile(r"^[A-Z0-9!#$%&'()@^_`{}~-]{1,8}(?:\.[A-Z0-9!#$%&'()@^_`{}~-]{1,3})?$")



class ValidationError(RuntimeError):
    """Raised for a bounded fail-closed M16 contract error."""

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def require_positive_int(mapping: dict, key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValidationError(f"{key} must be a positive integer")
    return value

def derive_layout(spec: dict) -> dict:
    geometry = spec["geometry"]
    filesystem = spec["filesystem"]
    bps = require_positive_int(geometry, "bytes_per_sector")
    cylinders = require_positive_int(geometry, "cylinders")
    heads = require_positive_int(geometry, "heads")
    spt = require_positive_int(geometry, "sectors_per_track")
    total_sectors = cylinders * heads * spt
    total_bytes = total_sectors * bps
    root_entries = require_positive_int(filesystem, "root_entries")
    root_sectors = (root_entries * 32 + bps - 1) // bps
    reserved = require_positive_int(filesystem, "reserved_sectors")
    fat_count = require_positive_int(filesystem, "fat_count")
    sectors_per_fat = require_positive_int(filesystem, "sectors_per_fat")
    sectors_per_cluster = require_positive_int(filesystem, "sectors_per_cluster")
    first_data = reserved + fat_count * sectors_per_fat + root_sectors
    data_sectors = total_sectors - first_data
    if data_sectors <= 0 or data_sectors % sectors_per_cluster:
        raise ValidationError("data region does not contain an integral cluster count")
    data_clusters = data_sectors // sectors_per_cluster
    fat_entries = data_clusters + 2
    fat_bytes_required = (fat_entries * 3 + 1) // 2
    fat_capacity = sectors_per_fat * bps
    if data_clusters >= 4085:
        raise ValidationError("derived cluster count is not FAT12")
    if fat_capacity < fat_bytes_required:
        raise ValidationError("FAT region cannot represent every data cluster")
    derived = {
        "data_clusters": data_clusters,
        "data_sectors": data_sectors,
        "fat_bytes_required": fat_bytes_required,
        "fat_capacity_bytes": fat_capacity,
        "first_data_sector": first_data,
        "root_directory_sectors": root_sectors,
        "total_bytes": total_bytes,
        "total_sectors": total_sectors,
    }
    declared = {
        "data_clusters": filesystem["data_clusters"],
        "fat_bytes_required": filesystem["fat_bytes_required"],
        "first_data_sector": filesystem["first_data_sector"],
        "root_directory_sectors": filesystem["root_directory_sectors"],
        "total_bytes": geometry["total_bytes"],
        "total_sectors": geometry["total_sectors"],
    }
    for key, value in declared.items():
        if derived[key] != value:
            raise ValidationError(f"declared M16 layout does not recompute: {key}")
    expected_d88 = spec["d88"]["header_size"] + total_sectors * (
        spec["d88"]["sector_header_size"] + bps
    )
    if spec["d88"]["declared_size"] != expected_d88:
        raise ValidationError("declared D88 size does not recompute")
    derived["d88_size"] = expected_d88
    return derived

def encode_dos_name(value: str) -> bytes:
    if not isinstance(value, str) or not value.isascii() or value != value.upper() or not DOS_NAME_RE.fullmatch(value):
        raise ValidationError(f"DOS filename is not lossless uppercase 8.3 ASCII: {value!r}")
    parts = value.split(".", 1)
    base = parts[0].encode("ascii").ljust(8, b" ")
    extension = (parts[1] if len(parts) == 2 else "").encode("ascii").ljust(3, b" ")
    return base + extension

def decode_dos_name(value: bytes) -> str:
    if len(value) != 11:
        raise ValidationError("DOS directory name is not 11 bytes")
    try:
        base = value[:8].decode("ascii").rstrip(" ")
        extension = value[8:].decode("ascii").rstrip(" ")
    except UnicodeDecodeError as exc:
        raise ValidationError("DOS directory name is not ASCII") from exc
    name = base + (("." + extension) if extension else "")
    if encode_dos_name(name) != value:
        raise ValidationError("DOS directory name is noncanonical")
    return name

def lba_to_chs(lba: int, geometry: dict) -> tuple[int, int, int]:
    total = geometry["total_sectors"]
    if not isinstance(lba, int) or isinstance(lba, bool) or not 0 <= lba < total:
        raise ValidationError("LBA is outside the M16 geometry")
    heads = geometry["heads"]
    spt = geometry["sectors_per_track"]
    base = geometry["physical_sector_id_base"]
    cylinder, remainder = divmod(lba, heads * spt)
    head, sector = divmod(remainder, spt)
    return cylinder, head, sector + base

def fat_datetime(source_date_epoch: int) -> tuple[int, int, str]:
    if not isinstance(source_date_epoch, int) or isinstance(source_date_epoch, bool):
        raise ValidationError("source_date_epoch must be an integer")
    value = datetime.fromtimestamp(source_date_epoch, timezone.utc)
    if not 1980 <= value.year <= 2107:
        raise ValidationError("source_date_epoch is outside the FAT timestamp range")
    fat_date = ((value.year - 1980) << 9) | (value.month << 5) | value.day
    fat_time = (value.hour << 11) | (value.minute << 5) | (value.second // 2)
    rendered = value.replace(second=value.second & ~1, microsecond=0).isoformat().replace("+00:00", "Z")
    return fat_date, fat_time, rendered

def set_fat12_entry(fat: bytearray, cluster: int, value: int) -> None:
    if not isinstance(cluster, int) or cluster < 0 or not isinstance(value, int) or not 0 <= value <= 0xFFF:
        raise ValidationError("invalid FAT12 entry request")
    offset = cluster + cluster // 2
    if offset + 1 >= len(fat):
        raise ValidationError("FAT12 entry exceeds the FAT byte region")
    if cluster & 1:
        fat[offset] = (fat[offset] & 0x0F) | ((value & 0x00F) << 4)
        fat[offset + 1] = (value >> 4) & 0xFF
    else:
        fat[offset] = value & 0xFF
        fat[offset + 1] = (fat[offset + 1] & 0xF0) | ((value >> 8) & 0x0F)

def build_boot_record(spec: dict) -> bytes:
    geometry = spec["geometry"]
    filesystem = spec["filesystem"]
    policy = spec["boot_record"]
    sector = bytearray(geometry["bytes_per_sector"])
    placeholder = bytes(policy["placeholder_code"])
    if placeholder != b"\xeb\xfe\x90":
        raise ValidationError("M16 placeholder must remain the documented self-loop")
    sector[0:3] = placeholder
    oem = policy["oem_name"].encode("ascii")
    if len(oem) != 8:
        raise ValidationError("OEM name must be exactly eight ASCII bytes")
    sector[3:11] = oem
    struct.pack_into("<H", sector, 11, geometry["bytes_per_sector"])
    sector[13] = filesystem["sectors_per_cluster"]
    struct.pack_into("<H", sector, 14, filesystem["reserved_sectors"])
    sector[16] = filesystem["fat_count"]
    struct.pack_into("<H", sector, 17, filesystem["root_entries"])
    struct.pack_into("<H", sector, 19, geometry["total_sectors"])
    sector[21] = filesystem["media_descriptor"]
    struct.pack_into("<H", sector, 22, filesystem["sectors_per_fat"])
    struct.pack_into("<H", sector, 24, geometry["sectors_per_track"])
    struct.pack_into("<H", sector, 26, geometry["heads"])
    struct.pack_into("<I", sector, 28, filesystem["hidden_sectors"])
    struct.pack_into("<I", sector, 32, 0)
    sector[36] = 0
    sector[37] = 0
    sector[38] = policy["extended_bpb_signature"]
    struct.pack_into("<I", sector, 39, spec["image"]["volume_serial"])
    label = spec["image"]["volume_label"].encode("ascii")
    if len(label) > 11:
        raise ValidationError("volume label exceeds 11 bytes")
    sector[43:54] = label.ljust(11, b" ")
    filesystem_type = policy["filesystem_type"].encode("ascii")
    if filesystem_type != b"FAT12":
        raise ValidationError("M16 filesystem type label changed")
    sector[54:62] = filesystem_type.ljust(8, b" ")
    offsets = policy.get("signature_offsets", [])
    if not isinstance(offsets, list) or len(offsets) != len(set(offsets)):
        raise ValidationError("boot-record signature offsets must be a unique list")
    for offset in offsets:
        if (not isinstance(offset, int) or isinstance(offset, bool) or
                offset < 0 or offset + 2 > len(sector)):
            raise ValidationError("boot-record signature offset is outside the sector")
        sector[offset:offset + 2] = b"\x55\xaa"
    return bytes(sector)

def build_directory_entry(record: dict, first_cluster: int) -> tuple[bytes, dict]:
    entry = bytearray(32)
    entry[0:11] = encode_dos_name(record["dos_name"])
    entry[11] = 0x20
    fat_date, fat_time, rendered = fat_datetime(record["source_date_epoch"])
    struct.pack_into("<H", entry, 14, fat_time)
    struct.pack_into("<H", entry, 16, fat_date)
    struct.pack_into("<H", entry, 18, fat_date)
    struct.pack_into("<H", entry, 22, fat_time)
    struct.pack_into("<H", entry, 24, fat_date)
    struct.pack_into("<H", entry, 26, first_cluster)
    struct.pack_into("<I", entry, 28, record["size"])
    return bytes(entry), {"fat_date": fat_date, "fat_time": fat_time, "utc": rendered}

def build_d88(spec: dict, raw: bytes) -> bytes:
    geometry = spec["geometry"]
    d88 = spec["d88"]
    if len(raw) != geometry["total_bytes"]:
        raise ValidationError("raw image size does not match the D88 payload geometry")
    header = bytearray(d88["header_size"])
    disk_name = d88["disk_name"].encode("ascii")
    if len(disk_name) > 17:
        raise ValidationError("D88 disk name exceeds 17 bytes")
    header[:17] = disk_name.ljust(17, b"\x00")
    header[26] = d88["write_protect"]
    header[27] = d88["disk_type"]
    struct.pack_into("<I", header, 28, d88["declared_size"])
    track_size = geometry["sectors_per_track"] * (
        d88["sector_header_size"] + geometry["bytes_per_sector"]
    )
    for track in range(d88["populated_tracks"]):
        struct.pack_into("<I", header, 32 + track * 4, d88["header_size"] + track * track_size)
    output = bytearray(header)
    lba = 0
    for cylinder in range(geometry["cylinders"]):
        for head in range(geometry["heads"]):
            for sector_index in range(geometry["sectors_per_track"]):
                sector_id = geometry["physical_sector_id_base"] + sector_index
                sector_header = struct.pack(
                    "<BBBBHBBBB3sBH",
                    cylinder,
                    head,
                    sector_id,
                    d88["sector_size_code"],
                    geometry["sectors_per_track"],
                    d88["mfm_density_field"],
                    d88["deleted_data"],
                    d88["error_status"],
                    0,
                    b"\x00\x00\x00",
                    d88["rpm_field"],
                    geometry["bytes_per_sector"],
                )
                output.extend(sector_header)
                start = lba * geometry["bytes_per_sector"]
                output.extend(raw[start:start + geometry["bytes_per_sector"]])
                lba += 1
    if lba != geometry["total_sectors"] or len(output) != d88["declared_size"]:
        raise ValidationError("D88 construction did not consume the complete raw image")
    return bytes(output)

def parse_d88(d88_bytes: bytes, spec: dict, derived: dict) -> tuple[dict, bytes]:
    geometry = spec["geometry"]
    contract = spec["d88"]
    if len(d88_bytes) < contract["header_size"]:
        raise ValidationError("D88 header is truncated")
    declared = struct.unpack_from("<I", d88_bytes, 28)[0]
    if declared != len(d88_bytes) or declared != contract["declared_size"]:
        raise ValidationError("D88 declared size or trailing-data boundary is invalid")
    expected_name = contract["disk_name"].encode("ascii").ljust(17, b"\x00")
    if d88_bytes[:17] != expected_name or d88_bytes[17:26] != bytes(9):
        raise ValidationError("D88 disk name or reserved header bytes differ")
    if d88_bytes[26] != 0 or d88_bytes[27] != contract["disk_type"]:
        raise ValidationError("D88 write-protect or disk-type field differs")
    offsets = list(struct.unpack_from("<164I", d88_bytes, 32))
    populated = offsets[:contract["populated_tracks"]]
    if any(offsets[contract["populated_tracks"]:]):
        raise ValidationError("D88 contains unexpected hidden track offsets")
    if len(populated) != len(set(populated)) or populated != sorted(populated):
        raise ValidationError("D88 track offsets descend, overlap, or duplicate")
    if not populated or populated[0] != contract["header_size"] or any(item >= declared for item in populated):
        raise ValidationError("D88 track offset is outside the declared file")
    raw = bytearray()
    seen = set()
    sector_records = 0
    track_size = geometry["sectors_per_track"] * (
        contract["sector_header_size"] + geometry["bytes_per_sector"]
    )
    for track, start in enumerate(populated):
        expected_start = contract["header_size"] + track * track_size
        end = populated[track + 1] if track + 1 < len(populated) else declared
        if start != expected_start or end - start != track_size:
            raise ValidationError("D88 track offsets are overlapping, gapped, or out of bounds")
        cursor = start
        cylinder, head = divmod(track, geometry["heads"])
        for sector_index in range(geometry["sectors_per_track"]):
            if cursor + contract["sector_header_size"] > end:
                raise ValidationError("D88 sector header is truncated")
            fields = struct.unpack_from("<BBBBHBBBB3sBH", d88_bytes, cursor)
            c, h, r, n, count, mfm, deleted, status, seek, reserved, rpm, size = fields
            expected_chr = (cylinder, head, geometry["physical_sector_id_base"] + sector_index)
            if (c, h, r) in seen:
                raise ValidationError("D88 contains a duplicate CHR sector")
            seen.add((c, h, r))
            if (c, h, r) != expected_chr:
                raise ValidationError("D88 contains a missing, extra, or out-of-order CHR sector")
            if n != contract["sector_size_code"] or size != geometry["bytes_per_sector"]:
                raise ValidationError("D88 sector-size code or byte length differs")
            if count != geometry["sectors_per_track"]:
                raise ValidationError("D88 per-track sector count differs")
            if (mfm, deleted, status, seek, reserved, rpm) != (0, 0, 0, 0, b"\x00\x00\x00", 0):
                raise ValidationError("D88 density, deleted-data, error, or reserved status is nonzero")
            cursor += contract["sector_header_size"]
            if cursor + size > end:
                raise ValidationError("D88 sector payload is truncated or out of bounds")
            raw.extend(d88_bytes[cursor:cursor + size])
            cursor += size
            sector_records += 1
        if cursor != end:
            raise ValidationError("D88 track contains trailing or hidden sector data")
    if sector_records != derived["total_sectors"] or len(raw) != derived["total_bytes"]:
        raise ValidationError("D88 sector set does not reconstruct the M16 geometry")
    return {
        "declared_size": declared,
        "disk_type": d88_bytes[27],
        "populated_tracks": len(populated),
        "sector_count": sector_records,
        "sha256": sha256_bytes(d88_bytes),
        "size": len(d88_bytes),
    }, bytes(raw)

def inspect(image: bytes, spec: dict) -> tuple[dict, dict[str, bytes]]:
    layout = derive_layout(spec)
    _, raw = parse_d88(image, spec, layout)
    geometry, fs = spec["geometry"], spec["filesystem"]
    bps, cluster_bytes = geometry["bytes_per_sector"], geometry["bytes_per_sector"] * fs["sectors_per_cluster"]
    if raw[11:36] != build_boot_record(spec)[11:36]:
        raise ValueError("BPB disagrees with the supported geometry")
    fat_start, fat_size = fs["reserved_sectors"] * bps, fs["sectors_per_fat"] * bps
    fat = raw[fat_start:fat_start + fat_size]
    for copy in range(fs["fat_count"]):
        if raw[fat_start + copy * fat_size:fat_start + (copy + 1) * fat_size] != fat:
            raise ValueError("FAT copies disagree")

    def value(cluster):
        # Deliberately independent of the producer's set/get entry helpers.
        offset = cluster * 3 // 2
        packed = int.from_bytes(fat[offset:offset + 2], "little")
        return (packed >> (4 if cluster & 1 else 0)) & 0xFFF

    if value(0) != 0xF00 | fs["media_descriptor"] or value(1) != 0xFFF:
        raise ValueError("reserved FAT entries are malformed")
    maximum = layout["data_clusters"] + 1
    if fat[layout["fat_bytes_required"]:] != bytes(fat_size - layout["fat_bytes_required"]):
        raise ValueError("unused FAT bytes are nonzero")
    if (maximum + 1) & 1 and fat[layout["fat_bytes_required"] - 1] & 0xF0:
        raise ValueError("unused FAT nibble is nonzero")
    owners, files, records, directories = {}, {}, {}, {}
    volume_label = None

    def read_chain(first, owner):
        chain, data = [], bytearray()
        cluster = first
        while True:
            if not 2 <= cluster <= maximum:
                raise ValueError("chain is outside the data area")
            if cluster in owners:
                raise ValueError("cyclic or cross-linked chain")
            owners[cluster] = owner
            chain.append(cluster)
            offset = layout["first_data_sector"] * bps + (cluster - 2) * cluster_bytes
            data.extend(raw[offset:offset + cluster_bytes])
            cluster = value(cluster)
            if 0xFF8 <= cluster <= 0xFFF:
                return chain, bytes(data)

    root_start = fat_start + fs["fat_count"] * fat_size
    root = raw[root_start:root_start + layout["root_directory_sectors"] * bps]
    pending = [("", 0, 0, root)]
    while pending:
        path, current, parent, data = pending.pop()
        names, dots = set(), set()
        for offset in range(0, len(data), 32):
            entry = data[offset:offset + 32]
            if not entry[0]:
                break
            if entry[0] == 0xE5:
                continue
            attributes = entry[11]
            if attributes == 0x0F or attributes & 0xC0 or entry[20:22] != b"\0\0":
                raise ValueError("unsupported live directory entry")
            first, size = struct.unpack_from("<HI", entry, 26)
            if entry[:11] in (b".          ", b"..         "):
                dot = entry[:11].rstrip().decode("ascii")
                if not path or dot in dots or attributes != 0x10 or size or first != (current if dot == "." else parent):
                    raise ValueError("invalid directory self/parent link")
                dots.add(dot)
                continue
            if attributes & 8:
                if (path or attributes & 0x10 or first or size or volume_label is not None
                        or any(value < 32 or value > 126 for value in entry[:11])):
                    raise ValueError("invalid volume-label entry")
                volume_label = entry[:11].decode("ascii").rstrip()
                continue
            name = decode_dos_name(entry[:11])
            if name in names:
                raise ValueError("duplicate live filename")
            names.add(name)
            full_name = path + name
            if attributes & 0x10:
                if size:
                    raise ValueError("directory has a nonzero file length")
                chain, contents = read_chain(first, full_name)
                directories[full_name] = {"clusters": chain}
                pending.append((full_name + "/", first, current, contents))
                continue
            if not size and not first:
                chain, contents = [], b""
            else:
                chain, contents = read_chain(first, full_name)
            if len(chain) != (size + cluster_bytes - 1) // cluster_bytes:
                raise ValueError("file length and chain disagree")
            files[full_name] = contents[:size]
            records[full_name] = {"size": size, "clusters": chain, "attributes": attributes,
                                  "sha256": hashlib.sha256(contents[:size]).hexdigest()}
        if path and dots != {".", ".."}:
            raise ValueError("directory self/parent links are missing")
    free = []
    for cluster in range(2, maximum + 1):
        if cluster not in owners:
            if value(cluster):
                raise ValueError("orphaned allocation or unqualified bad cluster")
            free.append(cluster)
    return {"files": records, "directories": directories, "free_clusters": free,
            "fat_copies_equal": True, "allocated_clusters": len(owners),
            "volume_label": volume_label,
            "d88_sha256": hashlib.sha256(image).hexdigest()}, files
