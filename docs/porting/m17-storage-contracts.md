# M17 PC-88VA storage, driver and media contracts

Contract identifier: `pc88va-storage-m17-v1`, machine-readable schema version 2
in `config/m17/media-profiles.schema.json` and selected profiles in
`config/m17/media-profiles.json`. This is a source/host-fixture contract, not a
claim that an M17 guest can mount an HDD.

## 1. Baseline, evidence and ownership

M17 starts from the accepted parent baseline
`f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4`: M16 **PASS / HANDOFF READY**.
The exact accepted component identities are fdkernel
`7883c8fac11fab20cb467ad0a93c8799f35b565a`, FreeCOM
`29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`, and COUNTRY.SYS
`23f189cca3420606eae8723884fa92ccd65eb307`. M16 CI runs 36381203803 and
36381203807 both succeeded at the exact M16 publication tip. Physical hardware
is NOT RUN. M17's source lock records its CONFIG/INIT kernel integration merge
and the exact changed files; no old M17 acceptance transfers to it.

The controller evidence is the public VAEG source commit
`62a597f0ee81e2e036af740a3e79ad3da83e3fb7`. It documents emulator format and
I/O behavior only. VAEG's SCSI BIOS is emulator functionality, not PC-88VA
hardware evidence. The owner confirms real hardware has no SCSI BIOS. Therefore
SCSI boot is excluded; SCSI is a **data-only** device behind one future external
DOS block driver loaded from an already accessible FDD or qualified SASI volume.
No SCSI `DEVICE=` driver exists in this M17 deliverable.

| Layer | Owner and deployment | M17 fact / qualification boundary |
| --- | --- | --- |
| DOS filesystem, FAT12/FAT16, files/directories | Selected common FreeDOS kernel | Existing DOS implementation; the six HDD fixtures do not prove guest FAT16 access |
| FDD1/FDD2 | Built-in VA adapter | A:/B: and M16 media behavior are an accepted baseline; the new raw `.img` files are separate host fixtures |
| Native SASI | Future built-in VA kernel integration | M19 data access; M20 boot. No SASI volume is mounted by this M17 candidate |
| C-bus SCSI | One optional `VASCSI.SYS` external block driver | M21 read-only data access; M22 writes. Filename/ABI profile is a future packaging contract, not an existing binary |
| MO | Extension of the same external SCSI ownership | M31/M32, last in the roadmap; no MO behavior is qualified here |

SCSI boot, a SCSI BIOS shim, host-file storage, a second competing scan owner,
a separate filesystem, ASPI manager and a parallel MO driver are outside the
selected architecture. Do not load the sole driver from a SCSI volume which is
not yet registered. The SCSI driver and controller each have exactly one owner.

## 2. M17 kernel source audit: CONFIG.SYS and DOS device ABI

`config/m17/source-audit.json` binds every reviewed kernel file to the exact
fdkernel component SHA in `manifests/m17-components.lock.json`. The relevant
pinned source locations are:

- `components/fdkernel/kernel/config.c`, `DoConfig` and `LoadDevice`: each
  configuration pass opens `FDCONFIG.SYS` first and falls back to `CONFIG.SYS`.
  The kernel runs passes 0 and 1 before `PreConfig2`, then pass 2 for device
  loading. `DEVICE=` invokes `LoadDevice`; that path uses `init_DosExec(3, ...)`,
  makes the driver command line, calls `init_device` for each header and links
  accepted headers into the device chain. `PC88VA_LOADSEG` is ignored by normal
  DOS parsing because stage 2 already consumed it. `DEVICEHIGH=` and options
  without a VA implementation report errors; they are not silently enabled.
- `components/fdkernel/kernel/intr.asm` and `kernel/init-mod.h`: the M17 VA
  integration uses FAR Pascal frames for INIT-time READ, LSEEK and EXEC wrappers;
  Watcom is built with separate SS and DS. CONFIG parser buffers and command-tail
  lifetimes are kept valid under the VA INIT stack contract. This changes the
  M16 kernel bytes, so it is bound to M17's placement/build/guest qualification.
- `components/fdkernel/hdr/device.h`: the device header is 18 bytes: FAR next
  pointer at 0, attributes at 4, 16-bit strategy and interrupt offsets at 6 and
  8, then eight name/unit bytes at 10. The request prefix is 13 bytes. INIT
  fields are unit count at offset 13, FAR resident end at 14, the pointer field
  at 18, and first logical unit at 22. Strategy is called before interrupt
  through the header offsets with ES:BX pointing to the request packet;
  `kernel/execrh.asm` saves DS/SI/BP around the pair, preserves SI/DI around
  strategy, then enables interrupts and clears direction on return.
- `components/fdkernel/kernel/main.c`, `init_device`: before each C_INIT call,
  the request is zeroed for status/unit count; `r_firstunit` is the current
  `LoL->nblkdev`; `r_endaddr` starts at the current top. For a CONFIG-loaded
  driver the VA kernel also passes the original CONFIG command line through the
  INIT union's pointer field. A future driver must consume/copy its options
  before reusing that field for an output BPB pointer. `r_bpbptr` is not proof
  that DOS has a valid BPB.
- `init_device` treats an end address equal to the header as nonresident; a
  block driver returning zero units is reduced to the header and not registered.
  For the last header it asks `KernelAllocPara` to retain the returned extent.
  The returned end pointer is trusted; the current path does not independently
  prove that it is within the loaded image/allocation. M21 must bound its own
  resident end and reject malformed INIT data before returning it.
- `main.c`, `update_dcb`: for positive units, `dh_name[0]` is set from
  `r_nunits`. DPBs are appended with global `dpb_unit`, driver-local
  `dpb_subunit`, and `dpb_device`; CDS entries are installed only while
  `nblkdev < lastdrive`, then `nblkdev` advances. The VA path does not cap a
  driver's returned unit count to remaining LASTDRIVE/CDS entries. An external
  driver must enforce its selected unit bound; a DOS unit beyond LASTDRIVE must
  never be reported as usable.
- `components/fdkernel/hdr/lol.h` and `kernel/kernel.asm`: the list-of-lists
  fields used here bind the first MCB, DPB chain, SFT list, CDS table, number of
  block devices and last-drive bound. `kernel/initdisk.c`, VA
  `ReadAllPartitionTables`: the current M16/M17 VA branch creates two floppy
  DDTs and returns; it does not discover SASI/SCSI or scan their partitions.
  There is no built-in SASI owner yet, and no common partition scan for an
  external SCSI unit.
- `kernel/blockio.c`, `kernel/dsk.c`, `kernel/fatfs.c`, `hdr/fat.h`: normal common
  file operations use DOS logical-sector counts, media-check/BPB requests and
  the standard FAT path. A block request carries a FAR transfer pointer,
  16-bit `r_count`, 16-bit `r_start`, and `r_huge` when the logical LBA needs the
  extended field. The count is DOS logical sectors, not controller blocks or
  bytes. Future adapters must bound the whole request, translate exact units,
  and report only complete DOS sectors.

**Inherited upstream error caveat; do not repair in M17:** `kernel/main.c` tests
INIT status using `(status & (S_ERROR|S_DONE)) == S_ERROR`, while
`hdr/device.h`'s ordinary `failure(x)` macro includes both `S_ERROR` and
`S_DONE`. That predicate does not reject the normal combined error flags. M21
must not rely on it to prevent registration: on every failed SCSI INIT, return
zero units, resident end equal to the header, and a failure status safe for this
pinned VA path; test both the conventional combined flags and the safe no-unit
case. Do not silently change common upstream error semantics in M17.

The INIT call chain has no duplicate-driver guard. M21 must establish one
configured `VASCSI.SYS` owner, reject a second load/scan and never allow a second
controller owner. It must avoid a partially registered multi-header driver;
the selected initial SCSI contract is a single header, one target/LUN and one
volume. Negative tests must cover duplicate `DEVICE=` lines, absent target,
unsupported partition, failed INIT, and LASTDRIVE exhaustion.

The CONFIG QA drivers are narrowly synthetic: CFGDEV.SYS is a character driver
for strategy/interrupt and device-open checks; CFGNONE.SYS returns zero block
units for the no-phantom-unit/no-retained-image negative case. Neither is a
SASI/SCSI implementation. Their separate CONFIG/FDCONFIG startup media and
memory probes are listed in `config/m17/config-qa.json`; guest results bind only
to exact M17 candidate bytes and are reported separately from HDD fixture tests.

## 3. Capacity and unit ledger

All sizes in the profile have units in their field names. No container header is
a guest sector. For these contiguous payload formats:

```text
payload_bytes = device_block_count * device_block_bytes
file_offset_bytes = container_header_bytes + device_lba * device_block_bytes
```

A selected volume maps as:

```text
volume_start_bytes = volume_start_device_blocks * device_block_bytes
                   = partition_start_logical_sectors * 512   # MBR profiles
volume_byte_offset = volume_start_bytes
                   + volume_lba * logical_sector_bytes
```

The independent validator checks exact image length, geometry product, aligned
conversion, start/count endpoints, and that the complete volume is inside the
payload. Python's unbounded integer arithmetic does not relax the DOS/controller
range fields; the range helpers separately reject non-integers (including bool),
zero counts, end overflow, and out-of-capacity requests.

| Selected profile family | Device block | DOS logical sector | Mapping and capacity |
| --- | ---: | ---: | --- |
| FDD 360 | 512 bytes | 512 bytes | 40×2×9 = 720 blocks; whole-device volume, 368,640 payload bytes |
| FDD 1280 | 1024 bytes | 1024 bytes | 80×2×8 = 1,280 blocks; whole-device volume, 1,310,720 payload bytes |
| SASI 615×8×33 | 256 bytes | 512 bytes | 162,360 blocks = 41,564,160 payload bytes; 2 blocks per DOS sector |
| SCSI 40 MiB, small block | 256 bytes | 512 bytes | 163,840 blocks = 40 MiB; 2 blocks per DOS sector |
| SCSI 40 MiB, large block | 512 bytes | 512 bytes | 81,920 blocks = 40 MiB; 1 block per DOS sector |

Profile geometry is the image/controller's declared block geometry; BPB and MBR
CHS are separate metadata. SCSI READ(10) address/count field limits, actual
controller/driver transfer buffers, common-kernel count fields, DOS FAT/BPB
limits and resident memory all constrain future support. M17 records no
controller transfer-buffer maximum as hardware fact and does not promise a
maximum multi-sector request. M21/M19 must split requests or reject them before
conversion when any layer cannot represent the complete interval.

## 4. Initial media and filesystem set

All six files are deterministic, public, nonbootable **host fixtures** produced
by `tools/m17/produce.py`; none depends on ROMs, private disk contents, saved
DOS executables, another milestone's D88 or a previous build directory. Their
manifest records exact file/container length, SHA-256, payload/volume offsets,
block and sector units, partition and BPB fields, FAT extents, cluster count,
known file hashes, and fragmented cluster chains. `tools/m17/inspect_storage.py`
independently parses the container and filesystem; it never imports the producer
and opens inputs read-only.

### FDD data-shape fixtures

- `fdd-360-fat12.img`: raw 720×512-byte blocks; unpartitioned FAT12, 512-byte
  BPB sector, 2 sectors/cluster, 112 root entries.
- `fdd-1280-fat12.img`: raw 1,280×1,024-byte blocks; unpartitioned FAT12,
  1,024-byte BPB sector, 1 sector/cluster, 192 root entries.

These are host data-shape fixtures, not M16 D88 images or new FDD guest results.
D88 is track/sector media and is intentionally not treated as a contiguous HDD
payload.

### SASI native-prefix fixtures

The public VAEG source models native SASI at its documented I/O interface and
provides a 615-cylinder × 8-head × 33-block geometry using 256-byte physical
blocks. Its VAEG boot service reads a 1,024-byte native prefix (four physical
blocks); the 40-MB class name is not a decimal or MiB capacity claim. M17 keeps
that prefix separate from the filesystem:

- Container: Anex86-style HDI, 4,096-byte header followed by exactly
  162,360×256 bytes of payload. Header geometry/capacity fields are checked.
- First four 256-byte payload blocks: reserved for future native IPL. The M17
  fixture fills this 1,024-byte prefix with zeros and is explicitly
  nonbootable.
- Volume starts at device block 4 (file byte 5,120 including the HDI header);
  no MBR is present. The DOS block adapter must translate one 512-byte DOS
  sector to two adjacent 256-byte SASI blocks. BPB hidden sectors are zero.
- 81,178×512-byte BPB sectors fill the remaining payload exactly. Initial
  filesystem variants are FAT12 with 16-KiB clusters and FAT16 with 1-KiB
  clusters; both use two FATs and 512 fixed root entries.

M19 must implement the data translation and actual built-in registration without
exposing HDI header bytes or the reserved prefix as filesystem sectors. M20
must prove a bootable loader in the reserved prefix and preserve the exact
volume start. The zeroed M17 prefix is not a boot program.

### SCSI data-only fixtures

The public VAEG source models a PC-88VA C-bus SCSI register interface at
`0x0cc0`–`0x0cc6`. This is source evidence about VAEG's model, not proof of
physical controller equivalence. The owner-confirmed absence of a hardware SCSI
BIOS excludes SCSI boot. Initial profiles bind target ID 0/LUN 0, one data disk
and one primary partition; no SCSI driver or boot path is in M17.

- Container: VHD1.00-style 220-byte header and exactly 40 MiB of contiguous
  payload. The small-block geometry is 640×8×32×256; the large-block geometry
  is 320×8×32×512.
- MBR: one non-active primary type `06h` entry at DOS LBA 2048 (1 MiB). It
  extends to the final 512-byte DOS sector. Other entries are zero. MBR CHS is
  encoded using the explicit synthetic 512-byte geometry of 32 sectors × 8
  heads and must agree with LBA; on disagreement the inspector rejects the
  image rather than selecting one field silently.
- Volume: 79,872×512-byte FAT16 sectors, two FATs, 2 sectors/cluster, 512 fixed
  root entries, hidden-sector field 2048. With 256-byte device blocks the
  partition start is device block 4,096; with 512-byte blocks it is block 2,048.
- MBR/PBR code is a fixed halt stub; partition is non-active and fixture is
  nonbootable. A future VASCSI.SYS must parse the selected partition and expose
  its BPB/reads as a DOS block unit. No firmware boot service is assumed.

Extended/logical and multiple partitions, active/bootable partitions, GPT,
FAT32, 1,024-byte HDD device blocks, mismatched MBR CHS/LBA, arbitrary VHD
variants, short/long payloads and unlisted controller units are outside this
initial profile set. The inspector returns distinct valid-supported,
valid-but-unsupported, malformed/truncated and inconsistent outcomes. CLI exit
codes are 0, 2 and 3 respectively for the first three categories; malformed,
truncated and inconsistent all fail with code 3 and a distinct diagnostic.

## 5. Deterministic unit/drive policy

- DOS boot identity remains the accepted FDD boot volume A:. Physical FDD2 is
  B: under the M16 baseline; M17 does not change it.
- Subsequent block units are deterministic: built-in SASI native unit 0, then
  native unit 1 when present, then successful external SCSI units in `DEVICE=`
  load/driver order. A single primary data volume is one DOS block unit; M17
  does not map multiple partitions from one target.
- `r_firstunit` is the global DOS unit index supplied at INIT. It is not a
  controller target ID and must not be hardcoded to C:. With only one SASI unit,
  its first DOS letter is C:. With units 0 and 1, they are C: and D:; the
  selected one-unit SCSI profile follows as D: or E: respectively.
- `LASTDRIVE=E` in the M17 config provides A: through E:, exactly enough for two
  FDDs, two SASI units and one SCSI unit. A driver must reject or expose zero
  units if it cannot fit the selected devices under the configured CDS limit;
  no aliasing or silent extra unit is permitted.
- No device/no media and failed INIT must not create phantom units. External
  SCSI is not bootable and cannot be the source of its own initial driver.

The host `assign_block_units` tests exercise no SASI, each SASI unit, SCSI alone,
all selected units, duplicates and LASTDRIVE exhaustion. This is a model of the
contract, not proof of runtime registration.

## 6. Reproduction, host validation and explicit deferrals

Standalone generation and read-only validation:

```sh
python3 tools/m17/produce.py --profiles config/m17/media-profiles.json \
  --output build/m17-storage
python3 tools/m17/inspect_storage.py --profiles config/m17/media-profiles.json \
  --directory build/m17-storage
```

The full offline M17 build also creates and inspects these fixtures from its
allowlisted source export. The report records each generated artifact's path,
size and SHA-256. The scoped VAEG PASS covers the candidate's FDD boot,
CONFIG/INIT profiles and guest file smoke test only; it does not qualify a DOS
HDD driver, FAT16 guest operation, SASI controller access, SCSI controller
access, HDD filesystem writes or HDD boot. All such guest storage checks are
NOT RUN under M17. Physical hardware is NOT RUN; status remains
**DEFERRED HARDWARE VALIDATION**.

M19 handoff: implement built-in SASI native-unit discovery, measured capacity,
checked two-block/one-DOS-sector translation, 4-block reserved-prefix mapping,
FAT16 BPB/read/write path and DPB/CDS registration from FDD boot. First
qualifying workload: the exact `sasi40-fat16.hdi`, read the known root file and
fragmented `PATTERN.BIN` across physical-block and cluster boundaries, then
compare guest bytes to the manifest. Add write-protection/media-error tests and
fresh-boot persistence before claiming the planned M19 write scope. Preserve the
native prefix for the separate M20 boot proof. These SASI operations are all
NOT RUN in M17.

M21 handoff: author one `VASCSI.SYS` source under the component's public
PC-88VA driver source location and package its public build through the M21
parent build. Load it once using `DEVICE=VASCSI.SYS` from an already accessible
FDD/SASI volume; test with no SASI and with SASI unit 0/1 present. Expose only
target 0/LUN 0 and its selected primary FAT16 partition initially. Implement
bounded INIT/end-address and LASTDRIVE checks, one owner/duplicate rejection,
READ CAPACITY length validation, MBR/BPB parsing, 256-to-512 aggregation,
request splitting, C_MEDIACHK/C_BLDBPB/C_INPUT, bounded sense/error mapping, and
C_OUTPUT write rejection. Qualify files and unchanged media on the exact
fixture; include absent target, corrupt capacity, invalid/overlapping MBR,
unsupported media, failed/duplicate INIT, no ghost drive, too-small buffer and
range-overflow cases. M17 measures no VASCSI resident footprint and establishes
no SCSI runtime operation; M21 must measure it against each boot source and the
active memory contract. SCSI writes and flush/persistence belong to M22.

M18 receives this exact source-linked INIT/resident-end, request/buffer and
configuration-residency contract as input to its separate memory accounting.
M17 does not perform M18 repairs or tool distribution. M20 is SASI boot; M23 is
combined storage integration; M31/M32 remain the final MO extensions.
