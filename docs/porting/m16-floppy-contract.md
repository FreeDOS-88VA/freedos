# M16 floppy data-volume contract

This is the selected data-volume contract, not an acceptance report. Guest
qualification must cover both physical drives and both models. These data
fixtures do not claim firmware boot or guest FORMAT support.

## Public format provenance

The geometry and FAT layouts are identified by the original PC-88VA
FDFORM/2HCDRV sources by mami, not by capacity names alone:

- [FDFRMSRC.LZH, Softlib 2-401](http://www.pc88.gr.jp/softlib/index.php?action=list_file&anum=2&gnum=401),
  SHA-256 `d81358cbcfc1d6175359059d9c01fb75e5585993c3bc3d3e1fc988d7aa7c3e5a`.
  `FDFORM.ASM` tables `BPB_2D8`, `BPB_2D9`, `BPB_DD8`, `BPB_DD9`,
  `BPB_HC5`, and the corresponding `MPB_*` tables define the selected layouts.
- [2HCDRSRC.LZH, Softlib 2-400](http://www.pc88.gr.jp/softlib/index.php?action=list_file&anum=2&gnum=400),
  SHA-256 `69a380af1ee74ee9d4e2fc6d536d4aa87aba0280c52808863e6cc3f41be2331e`.
  `2HCDRV.INC` distinguishes native format selectors (`$Med*`) from FAT
  descriptor bytes (`$FAT*`). `2HCDRV.DOC` identifies the 1.2 MB, 512-byte
  sector capability. Archives are reference material, not distribution inputs.

The selected 2HC profile is the 15-sector table. The additional 18-sector
profile in the source is outside this five-profile matrix.

| Profile | Cylinders × heads × sectors | Sector bytes | Payload bytes | Format selector | FAT byte | Native disk mode |
| --- | --- | --- | --- | --- | --- | --- |
| 2D 320 | 40 × 2 × 8 | 512 | 327680 | FFh | FFh | 02h |
| 2D 360 | 40 × 2 × 9 | 512 | 368640 | FDh | FDh | 02h |
| 2DD 640 | 80 × 2 × 8 | 512 | 655360 | FBh | FBh | 12h |
| 2DD 720 | 80 × 2 × 9 | 512 | 737280 | F9h | F9h | 12h |
| 2HC 1200 | 80 × 2 × 15 | 512 | 1228800 | F1h | F9h | 22h |

**The format selector is not the BPB/FAT media byte.** In particular, 2HC
uses F9h in its BPB and FAT reserved entry. F1h is its native format selector.
The former M16 configuration incorrectly conflated them. Its earlier 2HC
fixtures are not qualification evidence for this corrected contract.

All five fixtures use MFM, sector IDs 1 through the selected sectors-per-track count,
cylinder-major/head-minor D88 track order, two FAT12 copies, one reserved
sector and zero hidden sectors. The ordinary BPB stores two heads; the
formatter's maximum-logical-track field is not copied into that field.

| Profile | Sectors/cluster | Root entries | Sectors/FAT |
| --- | --- | --- | --- |
| 2D 320 | 2 | 112 | 1 |
| 2D 360 | 2 | 112 | 2 |
| 2DD 640 | 2 | 112 | 2 |
| 2DD 720 | 2 | 112 | 3 |
| 2HC 1200 | 1 | 224 | 7 |

The authoritative public build settings are `config/m16/floppy-profiles.json`.
The producer records `format_id` and `fat_media_descriptor` separately. D88
container bytes include track/sector headers and are not payload capacity.
The driver probes through the native firmware interface, validates the BPB
against the selected geometry, and maintains separate per-drive profiles.
Guest code does not inspect D88 host files.

## Short BPBs

The public formatter's `ipl_bpb` is followed by a two-byte head count and a
16-bit hidden-sector count; IPL code follows at offset 30. Those instructions
must not be treated as the upper hidden-sector word or a huge-sector count.
For a short BPB the adapter normalizes those absent fields. A native short BPB
without a 55AA marker additionally requires both FAT reserved-entry headers and
the physical profile endpoint to be readable before access is enabled. Failed
probes leave the unit inaccessible.

Generate original short-BPB boundary fixtures using `--boundary --short-bpb`.
The synthetic tail uses inert bytes rather than copying any formatter code.
This fixture family is a data-volume test, not a bootable formatter product.

## Native regression and legacy recognition

The existing 1024-byte-sector native control remains separate: 8 sectors per
track, two heads, with explicit 77- or 80-cylinder BPB profiles. The BPB-less
legacy fallback uses the explicit 77-cylinder FAT12 layout (one sector per
cluster, two two-sector FATs, 192 root entries, FEh media descriptor). It
requires readable reserved FAT entries in both copies and the final profile
sector before enabling normal access. A plausible malformed BPB cannot use
this fallback. Recognition is not a filesystem repair or a full filesystem
consistency checker.

## Reproducible tests

`tools/m16/build_floppy_media.py` constructs and independently inspects the
five original data fixtures. Its `--boundary` variant puts the last complete
cluster of `PATTERN.BIN` at the end of the data area, exercising a fragmented
chain, track/head crossings and the final data sector. The guest matrix must
read and write through FreeCOM/common kernel, then reopen the resulting image
in a fresh VAEG process and compare actual files and FAT/directory state.
Host fixture validity alone is not `VAEG PASS` or `HARDWARE PASS`.
