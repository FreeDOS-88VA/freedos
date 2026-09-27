# M17 storage and media contracts

## Ownership and deployment

| Layer | Owner | M17 state / next milestone |
| --- | --- | --- |
| INT 21h, FAT12/FAT16, files/directories, buffers | selected common FreeDOS kernel | Existing implementation; new HDD runtime paths unqualified |
| FDD1/FDD2 | built-in VA block adapter | Separate A:/B: state; carry forward exact scoped M16 results |
| SASI | built-in VA discovery and block adapter | M18 data-drive implementation; M19 native boot |
| SCSI | optional external VA DOS block `.SYS` | M20 INIT/read-only integration; M21 writes |
| MO | extension of external SCSI ownership | M30/M31; no hot-exchange claim here |

Select `VASCSI.SYS` as the future public 8.3 driver filename. It is a packaging
contract, not an existing executable. Load it from an accessible FDD/SASI volume
using DEVICE=. One controller has one owner; neither the kernel nor another
external driver may scan or operate a controller owned by VASCSI.SYS. A single
binary may internally separate transport, discovery and volume logic. No ASPI
manager, SCSI boot service, host-file access or parallel filesystem is assumed.

Logical mapping is A:/B: for physical FDD1/FDD2, followed by built-in SASI volumes
in stable unit/volume order, then successful external driver units in DEVICE
order. Pass the existing `r_firstunit`; never hardcode SCSI to C:. No-device or
failed INIT must allocate no logical drive. M18 must preserve per-unit media and
error state; M20 must prove actual DPB/BPB registration before claiming support.
LASTDRIVE must cover the resulting DOS unit count, bounded by A: through Z:.

## Audited source of truth

`config/m17/source-audit.json` binds the reviewed files to the kernel component
pin. The build rejects a changed file or kernel identity until the audit is
updated. Refer to these named functions in the pinned component sources:

- `kernel/config.c`: DoConfig file precedence/passes; LoadDevice loads an overlay
  with `init_DosExec(3, ...)`, calls INIT for each header, and links accepted
  headers into the device chain. KernelAllocPara reserves retained paragraphs.
- `hdr/device.h`: the 18-byte device header has FAR next pointer, attributes,
  16-bit strategy/interrupt offsets and eight name/unit bytes. ES:BX identifies
  a packed request; command 0 is INIT. The common request prefix is 13 bytes;
  INIT uses unit count at 13, resident-end FAR pointer at 14, BPB/command-line
  pointer at 18 and first logical unit at 22. Read/write requests carry FAR
  transfer address, count, start and extended start fields.
- `kernel/execrh.asm`: strategy then interrupt FAR calls through header offsets.
  M17 also fixes previously unused INIT file/EXEC wrappers in kernel/intr.asm.
- `kernel/main.c`: init_device initializes the request, handles no retained
  memory/zero units, reserves the resident extent and invokes update_dcb.
  update_dcb appends DPBs with logical and subunit identities; BPB rebuilding
  remains in the normal common block path. The INIT BPB pointer is not evidence
  that an external unit has a valid working filesystem.
- `kernel/initdisk.c`: the VA ReadAllPartitionTables branch currently constructs
  two FDD DDTs and returns. It performs no SASI/SCSI partition scan. The unrelated
  IBM branch is not a VA implementation.
- `kernel/blockio.c`, `kernel/fatfs.c`, `hdr/fat.h`: common media checking, BPB
  handling and FAT type rules remain the DOS baseline. No FAT32 is enabled.

The pinned `init_device` error predicate tests `(status & (S_ERROR|S_DONE)) ==
S_ERROR`. Do not assume it rejects every combination of DONE and ERROR.
This inherited behavior must be considered in driver INIT failure conventions
and M20 negative qualification; do not silently repair upstream DOS in M17.
A bad image/driver must not rely solely on that predicate to prevent registration.

## Physical blocks, DOS sectors and partition policy

All arithmetic uses checked unsigned ranges. A transport block is not a DOS
sector and a host-container header is never an on-device block. For the selected
HDD profiles, DOS sectors are 512 bytes. SASI uses two consecutive 256-byte blocks
per DOS sector. SCSI profiles cover 256-byte (ratio 2) and 512-byte (ratio 1)
blocks. Requests validate volume LBA/count, partition offset, physical-block
conversion and capacity before I/O. These ratios need real M18/M20 adapter
implementation; a host-valid image does not implement it.

Do not support a DOS sector smaller than a physical block by implicit partial
writes. 1024-byte HDD physical blocks, other ratios and capacity rounding need
an explicit later policy. On short I/O, report only completed DOS sectors; do
not count half a DOS sector as success. Bound retries and preserve transport
status; handle write protection, no-device, range errors and malformed media.

The selected fixtures are new project data media:

| Profile | Container | Physical geometry | DOS sectors / FAT |
| --- | --- | --- | --- |
| fdd-360-fat12 | raw | 40 x 2 x 9 x 512 | 720 x 512, FAT12 |
| fdd-1280-fat12 | raw | 80 x 2 x 8 x 1024 | 1280 x 1024, FAT12 |
| sasi40-fat12 | HDI, 4096-byte header | 615 x 8 x 33 x 256 | 81180 x 512, FAT12, 16 KiB clusters |
| sasi40-fat16 | same HDI geometry | same | 81180 x 512, FAT16, 1 KiB clusters |
| scsi40-256-fat16 | VHD1.00, 220-byte header | 640 x 8 x 32 x 256 | 40 MiB disk, FAT16 primary data volume |
| scsi40-512-fat16 | same VHD container | 320 x 8 x 32 x 512 | same logical layout |

HDI fixtures have one unpartitioned volume at data block zero. SCSI fixtures use
one nonbootable MBR primary FAT16 type 06h volume at DOS LBA 2048, extending to
capacity. The other entries are empty; extended/GPT/NEC tables are not guessed.
The transport must honor checked LBA/count fields rather than saturated MBR CHS.
BPB hidden sectors equal the volume start in DOS-sector units. Two FATs, fixed
root directories, public labels/serials and fixed timestamps are explicit in
config/m17/media-profiles.json and the producer. FAT type comes from cluster
count, not the printable FAT label. New media deliberately contain no firmware
or PC-Engine boot bytes and are not compatible-PC-Engine-format claims.

The public container/geometry precedent is VAEG
`62a597f0ee81e2e036af740a3e79ad3da83e3fb7`,
[fdd/sxsi.h](https://github.com/nakatamaho/vaeg/blob/62a597f0ee81e2e036af740a3e79ad3da83e3fb7/fdd/sxsi.h),
[fdd/sxsi.c](https://github.com/nakatamaho/vaeg/blob/62a597f0ee81e2e036af740a3e79ad3da83e3fb7/fdd/sxsi.c), and
[fdd/newdisk.c](https://github.com/nakatamaho/vaeg/blob/62a597f0ee81e2e036af740a3e79ad3da83e3fb7/fdd/newdisk.c).
No VAEG checkout, private disk, saved executable or ROM is a fixture build input.

## Validation and handoffs

The separate inspector reads container, MBR, BPB, FAT copies, fragmented chains,
a nested directory and a file at the last allocatable cluster. It checks actual
payloads independently of producer hashes and rejects truncation, FAT loops,
crosslinks, orphan allocations and manifest drift. The full isolated build
produces all fixtures twice and compares exact bytes/manifests. Read-only fsck
can additionally inspect extracted volumes; it is supplementary host evidence.

M18 must establish native SASI discovery, block translation, capacity bounds and
built-in unit registration, then qualify FAT16 reads/writes/persistence from FDD
boot. Native boot remains M19. M20 must add VASCSI.SYS, target/options policy,
real block INIT/BPB/DPB acceptance, stable drive mapping, no-device/failed-init
behavior, bounded errors and write rejection. Character-device tests are not
external block-device acceptance. M21/M22 cover writes and integrated release.
M16's outstanding full media/input acceptance is not retroactively passed here.
