# M17 goal: storage contracts and reproducible media formats

Revision: 2026-09-27. M17 scope unchanged; M18 now requires the compact basic-disk payload on exactly one bootable 2HD disk. Preserve already adopted M13-M32 numbering without a second shift.

Repository placement: `docs/tasks/M17-storage-contracts-media-formats-goal-Codex.md`
inside the active parent worktree selected for M17.

Invocation from that worktree:

```text
/goal Read docs/tasks/M17-storage-contracts-media-formats-goal-Codex.md in full and complete M17 storage contracts and media formats. This is the former storage M16, renumbered after the new floppy/input M16. Verify the actual M16 baseline, preserve external SCSI .SYS loading through DEVICE=, audit the VA driver-loading and unit-registration contracts, and implement reproducible FAT12/FAT16 synthetic media generation and independent validation. Complete required tests, records, scoped topic commits/pushes, applicable CI and concrete M19 SASI/M21 SCSI handoffs. Preserve the completed earlier M16 insertion, and apply the immediately previous M18-M31 to M19-M32 mapping only if active records have not already adopted it. New M18 is memory, MEMMAP and exactly one bootable 2HD disk with compact MS-DOS 2.11-era tools and real-mode JWASMR; preserve historical evidence and actual M16/M17 status. Report every 30 minutes and follow the consultation rules. Do not reimplement accepted M16 features, start later runtime drivers or claim untested support. Keep SCSI boot excluded and MO last.
```

## 0. Renumber the storage milestone and define completion

The user inserted a new M16 for floppy formats, physical B:, VA cursor behavior,
VA/VA2 key auto-repeat and function keys. This storage-contract task moves from
its former M16 number to M17 in an earlier revision. That earlier mapping
must not be applied again. The 2026-09-27 revision inserts memory/distribution
M18 and moves immediately previous M18-M31 to M19-M32 once; M13-M17 are unchanged.
The storage scope and external-SCSI architecture remain intact. The later compact
M18 revision replaces its broad English-distribution requirements in place; it
does not shift M19-M32 again or create M33.

M17 establishes the controller, capacity, physical/logical sector lengths,
partition layout, BPB, and drive-assignment rules that later storage milestones
implement. Deliver concrete supported profiles, reproducible FAT16 media and an
independent inspector while preserving the newly qualified FAT12/FDD baseline.
This includes executable schema/fixture/validator work; it does not implement
operational SASI/SCSI drivers or HDD boot.

| Milestone | Current responsibility |
| --- | --- |
| M13-M15 | Existing shell, floppy-write and supported DOS API foundations |
| M16 | 2D 320/360, 2DD 640/720 and 2HC read/write; physical B:; VA cursor; VA/VA2 repeat and function keys |
| M17 | Storage contracts, built-in SASI/external SCSI ownership, VA external-driver ABI audit, media/partition/BPB profiles and reproducible FAT12/FAT16 fixtures |
| M18 | Conventional-memory/MCB cleanup, MEMMAP, and exactly one public bootable native 2HD disk containing the 8086-class selected MS-DOS 2.11-era tools and real-mode JWASMR through make m18-disk |
| M19 | SASI data-drive implementation and qualification |
| M20 | Native SASI boot and resident-I/O handoff |
| M21 | External SCSI .SYS loading/initialization, unit registration and HDD reads |
| M22 | Writes and persistence through the same external SCSI .SYS |
| M23 | Integrated FDD/SASI/SCSI release, including omitted-driver/no-device cases |
| M24-M30 | Previously agreed Japanese/NLS/input/8.3 and conditional staged LFN work |
| M31 | MO reads and medium reidentification |
| M32 | MO writes, safe exchange and final integration |

SCSI boot remains excluded. The companion
`freedos-pc88va-milestones-M13-M32.md` gives the full updated plan.

### 0.1. Migrate active records without rewriting evidence

Keep the earlier M16-to-M17 storage supersession as history. Apply the immediately
previous M18-M31 -> M19-M32 shift only to records which have not already adopted
it. For current M13-M32 records, update only M18 scope/references to memory and
the compact basic disk. Update canonical routing, active goals, future dependencies
and links; preserve the current M13-M17 status and historical run
IDs, hashes, report contents, commits and actual status. Retire the old active
`M16-storage-contracts-media-formats-goal-Codex.md` with a redirect/supersession
record pointing here. Do not leave two competing active meanings of M16.

Preserve existing storage work, even if its branch or evidence directory retains
an old m16 name. Identify it by purpose and source/artifact identity, not number
alone. Preserve the new M16 work under its actual accepted contract. Earlier
instructions deferring floppy/input support or declaring all M16 work withdrawn
are obsolete; they must not restore an obsolete active scope.

Early boot progress messages alone remain outside the new M16 contract unless
separately authorized. Do not add them or rerun completed floppy/input work solely
because this storage milestone was renumbered. Requalify affected behavior only
when evidence or a relevant change requires it.

### 0.2. Authority and exclusions

The user authorizes local source/document analysis, scoped contract/schema and
host-tool changes, original synthetic fixtures/tests, required regressions,
records, task-owned commits, normal topic-branch pushes, and applicable CI.
Proceed without requesting permission for ordinary implementation decisions.
This goal authorizes M17 after the new M16 prerequisites are satisfied; the
renumbering itself does not prove their acceptance.

Do not force-push, merge to a shared main branch, reset another worktree,
publish private inputs/derived values, write to original user media, or patch
ROMs. Do not replace the common FreeDOS filesystem or refactor the whole
storage subsystem to make a proposed abstraction look cleaner.

No new guest SASI/SCSI driver, low-level HDD formatter, general installer,
SASI boot loader, SCSI boot path, MO implementation, FAT32, LFN, NLS/Japanese,
new memory manager, or utility-distribution port is authorized by this M17.
Use English in code, comments, schemas, committed documentation, and technical
reports. User-facing progress may be Japanese.

## 1. Inspect the actual baseline and sources of evidence

The current host is ryzen, Ubuntu 24.04 amd64. The normal parent repository is
`$HOME/work/pc88va/freedos-pc88va`, where HOME belongs to ryzen. Discover the
actual parent/component worktrees, remotes, branches, gitlinks, dirty changes,
build commands, accepted toolchain, and current milestone records. Read root
and scoped AGENTS.md plus relevant M13-M16 contracts/reports, the current M16
handoff, existing storage notes/tools, and privacy/build/CI conventions.

Preserve unrelated work. Snapshot task-owned dirty changes before editing and
use isolated worktrees when needed. Do not reset to a historical SHA from a
conversation or treat an extracted build directory as the source of record.

Identify the real accepted M16 source/candidate, kernel, fully packaged VA
COMMAND.COM, loader, maps, VAEG executable/configuration, model, local ROM
selection, ordinary launch, and boot D88. A prior instruction is not evidence
of completed acceptance. Record unresolved prerequisites honestly.

M17's host contract/fixture work may proceed independently of an unfinished
runtime test where it is genuinely independent. Do not declare overall readiness
for the next M18 while the required new M16 baseline remains unqualified. Ordinary missing
SASI/SCSI runtime support is expected at this point, not an M17 failure.

Read the current VA memory specification/status/handoff, including
`docs/msdos211-memory-compat/` when present. Preserve the actual VA-native capacity
and reservation/MCB contracts. Do not assume 640 KiB, reclaim unproven memory,
or add IBM-compatible INT 12h/INT 15h memory sizing. Design guest-facing request
sizes and scratch buffers for the accepted 16-bit/V30 environment and supported
memory configurations; host tools do not imply unlimited guest memory.

The local documentation root is `$HOME/work/pc88va/pc88va-private-docs`; VAEG
is the sibling `vaeg/`. Resolve actual absolute paths and the accepted pinned
toolchain rather than reusing old Mac executable paths. Use
`rg --files` then targeted reads of relevant MD/TXT from `tekumani/`,
`chip-databooks/`, `nec98-databook/`, `pc-engine/`, and other actual sources.
PC-Engine here means the VA operating system. Earlier goal files are task
history, not hardware specifications. Missing PDFs do not globally block
available documented interfaces.

Inspect the current FreeDOS fork's device request structures, FAT/BPB parsing,
capacity arithmetic, drive enumeration, and boot/media tools. Inspect actual
VAEG SASI/SCSI controllers, image backends, supported configuration, and existing
synthetic tests. Do not infer current behavior from old release notes alone.

For each material fact, keep a locator and label it DOCUMENTED, SOURCE_FACT,
RUNTIME_OBSERVATION, INFERENCE, or UNKNOWN. Distinguish:

- What the hardware/firmware contract says.
- What this VAEG revision currently implements.
- What the common FreeDOS kernel can represent.
- What this VA port currently qualifies.
- What the selected later milestone is planned to support.

An emulator exposing a device does not prove the DOS driver exists. A FAT16
code path in the common kernel does not prove a VA FAT16 volume is qualified.

## 2. Internal phases and required outputs

| Phase | Work | Required output |
| --- | --- | --- |
| M17a | Migrate routing once, audit sources and existing storage behavior | Baseline and an evidence-linked inventory with explicit owners and gaps |
| M17b | Select controller, deployment/ABI, address, capacity, image, partition, filesystem, and drive contracts | Concrete versioned profiles, external-driver source audit, and an ADR usable by M19-M22 |
| M17c | Implement deterministic synthetic media generation and independent inspection | FAT12/FAT16 positive fixtures, manifests, read-only validator, and negative corpus |
| M17d | Validate boundaries, reproducibility, and existing-path compatibility | Passing named tests and an honest coverage/limits report |
| Closure | Reconcile records, commit/push, run applicable CI, and hand off | M17 completion, memory-contract inputs for M18 and concrete M19/M21 storage starting points |

These are work phases, not approval gates or normal stopping points. Proceed
from comparison to decisions, tools, tests, and closure. Use the consultation
rules only when a concrete unresolved decision requires them.

Reuse established contract/schema/report locations. Suggested records are:

- `docs/storage/storage-contract.md`;
- `docs/storage/media-profiles.json` or the established machine-readable format;
- `docs/storage/m17-format-decisions.md`;
- `docs/porting/m17-report.md` and the existing milestone status/handoff;
- the existing host-tool and fixture/test locations.

Do not create duplicate registries or two competing sources of active geometry.
Keep public profiles free of private-only values; retain private profiles and
their evidence under the existing excluded evidence root when required.

## 3. Controller and service boundaries

Build a comparison table for the actual SASI and SCSI HDD paths. Record
controller/model selection, target/LUN/unit addressing, discovery, capacity,
block size, transfer limits, status/error semantics, retries/timeouts, buffer
ownership, and available firmware versus direct-controller paths.

Do not equate SASI and SCSI because both transport block data, or copy NEC98
register values into the VA contract without evidence. Keep the selected VA
controller interface distinct from the disk-image container and DOS filesystem.

Define the smallest common contract needed by later implementations:

- Stable device identity, capability/state discovery, and unit selection.
- Capacity and block-length reporting with explicit units and numeric ranges.
- Read/write request inputs, buffer ownership, requested/completed counts,
  error results, and unsupported-operation behavior.
- Protection state, cache/flush responsibilities, reset/revalidation, and
  media-instance identity where applicable.
- Layer ownership of retries/timeouts and recovery after partial work.
- Which calls require initialized DOS/driver state and which future boot paths
  must use a different pre-DOS service.

Bind these semantics to existing kernel interfaces where possible. A new common
abstraction must have a demonstrated need; writing a generic block framework or
porting both transports is not M17's objective. If interface declarations or
small pure conversion helpers are needed, keep them scoped and tested without
activating an unqualified transport at boot.

Write completion and error rules explicitly. A completed device block is not
automatically a completed DOS logical sector. A multi-block write may partially
modify the medium before reporting failure; do not promise transactionality
from a request-level return code. Preserve the supported read-only state and
protection/error behavior rather than representing every target as writable.

MO remains later. Avoid baking in an assumption that every future device is
fixed media, but do not require MO capacity/sense/command implementation or a
new removable-media framework to finish M17.

### 3.1. Adopt the agreed deployment boundary

The user has selected an external DOS block-device `.SYS` for SCSI. This is an
accepted architectural decision, not an open built-in-versus-external choice
requiring renewed permission. Include SCSI in the common storage contract;
that does not require linking its controller code into the resident kernel.

- Keep INT 21h file services and FAT12/FAT16 handling in the common kernel.
  The SCSI driver must not implement a second filesystem, intercept file APIs
  as a shortcut, or access the host image/file path directly.
- Keep the FDD and planned SASI boot-access path in the existing loader/native
  kernel integration. M19 implements SASI data access; M20 qualifies the early
  boot path and handoff to resident I/O. Initial access must not depend on a
  driver file stored on the not-yet-accessible device.
- Load the SCSI `.SYS` using `DEVICE=` in the supported CONFIG.SYS/FDCONFIG.SYS
  processing path, after DOS starts from an accepted FDD or SASI source.
  Place the driver on an already accessible volume. Do not assume that its
  drive letter is always A: or C:. Select and document the actual 8.3 filename
  and packaging path; no particular binary name is already implemented here.
- The driver owns controller access, capacity/discovery, supported partition
  enumeration and volume offsets, BPB/unit presentation, block transfers, and
  transport-error translation. Bind each responsibility to the actual existing
  DOS device interface rather than inventing a new kernel-private interface.
- BIOS-less SCSI data access does not require an IBM-compatible disk BIOS shim.
  SCSI boot and a new SCSI bootstrap loader remain excluded. Loading later
  applications from an initialized SCSI volume is not SCSI firmware boot.
- Begin with one external SCSI driver, with separate internal controller and
  disk/volume modules where useful. Do not require a separate ASPI manager,
  ASPI compatibility, hot loading, or runtime unloading to complete this plan.
  Reuse existing compatible code when its provenance and interfaces permit.
- Give each controller one active owner. Avoid simultaneous built-in and external
  SCSI scans, duplicate units, or independently loaded HDD/MO drivers issuing
  competing commands. M31/M32 reuse this ownership and transport design; they
  may extend the driver without requiring an independent MO driver binary.

Record resident code/data, initialization-only code, transfer buffers, stack
needs, and supported memory configurations separately. Optional loading avoids
retaining SCSI code when omitted; do not promise that a loaded external driver
uses less memory than a built-in implementation. Require measurement in M21.

### 3.2. Audit the VA external block-driver path in M17

Inspect the actual pinned kernel sources and retained test evidence for:

1. CONFIG.SYS/FDCONFIG.SYS selection, `DEVICE=` parsing, load order, file loading,
   and driver initialization before the shell.
2. Device headers, strategy/interrupt entry points, request packets, near/far
   pointers, register preservation, and segment/stack assumptions.
3. INIT return semantics, resident-end calculation, unit counts and BPB pointers,
   device-chain/DPB registration, and drive-letter allocation.
4. Relevant media-check, BPB-build, read/write, status/error, and flush contracts;
   distinguish required operations from unsupported optional commands.
5. No-device, rejected media, failed/partial initialization, and duplicate-load
   behavior, including memory retention and prevention of phantom drives.
6. Shared-kernel paths with IBMPC/NEC98 assumptions that the VA target must remove
   or adapt before an actual external block driver can be qualified.

Produce a source-linked integration map, concrete ownership/ABI decisions, and
an explicit readiness/gap list. Upstream support or M15's broad API qualification
alone is not evidence that VA external block-driver loading has passed.

M17 is a contract/source-audit milestone: a new `.SYS` prototype, operational
controller code, or guest driver acceptance is not required here. Map bounded
missing loader/registration repairs to M21, with exact source locations and
planned distinguishing tests. Such named implementation work may remain pending
without weakening M17's contract gate. Essential ABI/ownership facts cannot all
remain TBD. A broad kernel redesign requires the existing consultation process;
do not silently abandon the selected external-driver architecture.

### 3.3. Preserve downstream implementation gates

M21 must exercise the actual packaged external driver through normal `DEVICE=`
loading, INIT and DOS registration, then read controlled FAT16 files through the
common kernel/FreeCOM. Cover the qualified boot sources, ordinary launch without
diagnostic helpers, absent/invalid devices, bounded errors, stable mapping, and
measured resident memory. Reject writes and verify input media are unchanged.
Fix the bounded VA loader/registration gaps identified in section 3.2 as needed.

M22 adds writes through that same interface, verifying file/FAT/directory changes,
close/flush and reopen persistence, fresh-boot results, protected/non-target
preservation, and bounded failures with truthful partial-completion behavior.
M23 integrates the accepted FDD/SASI/SCSI paths, including omitting the SCSI
driver entirely and loading it with no configured SCSI target. None of these
planned tests is performed or marked PASS merely by completing M17.

## 4. Capacity, sector units, and address conversion

Create an explicit unit ledger from the container to the filesystem:

| Quantity | Meaning that must be specified |
| --- | --- |
| Container offset | Host file position, including any format header/trailer or indexed structure |
| Payload extent | Device-addressable bytes represented by that container |
| Device block | Unit used by the selected controller/firmware request |
| Device capacity | Number of accessible device blocks and total represented bytes |
| Partition location | Start/length with the partition format's actual units |
| DOS logical sector | Unit described by the accepted BPB and kernel block interface |
| Filesystem cluster | Allocation unit derived from DOS logical sectors |
| Transfer buffer | Byte extent in guest memory with segment/alignment/ownership limits |

Use explicit units in field names and validate conversions at each boundary.
Do not assume that all occurrences of sector mean 512 bytes. A firmware unit,
controller block, partition unit, and BPB sector may differ. Distinguish physical
drive geometry from a firmware or image's synthetic CHS geometry.

For a selected contiguous-payload format, the host mapping may be expressed as:

```text
file_offset_bytes = payload_offset_bytes
                  + device_lba * device_block_bytes
```

This formula applies only after the container's contiguous mapping is established.
It is not a universal rule for indexed containers such as a track/sector image.
Do not expose host container headers as guest sectors.

For a selected contiguous partition/volume mapping, define and test the byte
relationship before reducing it to controller requests:

```text
volume_byte_offset = partition_start_bytes
                   + volume_lba * dos_sector_bytes
```

Specify how `partition_start_bytes` is derived from the chosen partition format.
Check alignment, representability, request end, and whether the whole logical
transfer lies inside both the volume and underlying payload.

When sizes differ, decide whether the initial profile uses aggregation,
subdivision with a qualified read-modify-write contract, or explicit rejection.
Do not implement silent rounding or assume an arbitrary size ratio is supported.
An aggregation ratio that works for reads still needs truthful partial-write
and recovery semantics. Keep read-modify-write ownership, alignment, and media
identity explicit if it is part of a selected future profile.

Record limits imposed independently by controller command fields, firmware ABI,
common-kernel types/algorithms, partition/BPB fields, transfer buffers, and image
backends. The supported maximum is constrained by all relevant layers; it is
not simply the largest host integer type or the size of a sparse file.

Use checked arithmetic for offsets, counts, multiplication, and inclusive/
exclusive endpoints. Establish whether a capacity response is a count or a
last-address value before applying any increment. Treat special/sentinel values
using the actual service contract. Never perform an increment or product in
a too-small type before widening it.

Host tools may use wide arithmetic. Guest-facing helper design must work with
the accepted compiler/CPU and memory model; do not introduce 386-only code or
an unexamined large runtime just for a count conversion. Reuse established
integer helpers or explicit checked operations as appropriate.

## 5. Image containers, partitions, BPBs, and filesystem profiles

### 5.1. Select a small, concrete initial support set

Inventory the actual image formats used by VAEG and existing project tools.
Record signatures, header size, payload offset/size, sector representation,
geometry fields, protection state, and validation requirements from the actual
implementation/specification. A familiar filename extension is not a format
specification; similarly named containers may be unrelated.

Retain accepted FDD/FAT12 fixtures as the current baseline. Select an initial
SASI HDD profile for M19/M20 and a SCSI HDD data profile for M21/M22, using
the evidenced hardware/firmware/backend support. They may share a filesystem
profile while having different transport or container details.

Choose the smallest useful documented support set and state its limits. Do not
promise every capacity, image extension, partition scheme, or sector size.
At least one usable planned profile per required HDD transport must be concrete;
an inventory in which every essential field remains TBD is not M17 PASS.

### 5.2. Partition and boot-area decisions

Compare the VA/native or NEC98-derived layout actually relevant to the chosen
path, an IBM-style partition table where relevant, and an unpartitioned FAT
volume as distinct candidates. Do not default to an IBM MBR merely because the
common FreeDOS source has an IBMPC implementation. Do not infer the on-disk
partition format from a controller's bus or command set.

For the selected initial layout, specify:

- Container/device metadata versus partition-table and volume metadata.
- Partition table location, identification, entry layout, and size limits.
- Start/length units, CHS/LBA interpretation, representability, and precedence
  when redundant fields disagree.
- Allowed partitions, overlap and out-of-range rejection, and reserved extents.
- BPB/volume location and the meaning of hidden-sector or offset fields in
  that specific format and driver contract.
- Selection/enumeration rules and which metadata is authoritative.
- How the layout accommodates M20's later SASI boot requirements without
  pretending that boot code is already implemented.

Do not fill unexplained boot-reserved areas with arbitrary filesystem data.
Conversely, do not invent a universal reservation or preserve a copied private
boot sector as a supposedly original public fixture. Synthetic images may be
deliberately nonbootable and must be labelled that way.

SCSI media remain data media reached after an accepted boot source; do not add
an SCSI boot path. Preserve the distinction between format readiness, planned
boot compatibility, and actual firmware-to-kernel boot qualification.

### 5.3. FAT12/FAT16 and BPB validation

Use the existing common FreeDOS FAT implementations and accepted documented
classification rules. Derive FAT type from the computed data-cluster count
and structural constraints, not a volume-label string or extension. Check the
actual pinned kernel's supported BPB fields, sector sizes, arithmetic, and
limits. Do not claim that a valid general FAT format is necessarily supported
by this VA target.

Define volume bounds, reserved sectors, FAT count/size, root-directory layout,
data start/count, sectors per cluster, valid cluster range, and file-size limits.
Verify the FAT has enough entries, the metadata/data regions fit without
overflow/overlap, and the selected profile's required FAT copies are consistent.
Handle optional or version-dependent BPB fields using the selected contract.

Define treatment of inconsistent redundant fields, truncated images, malformed
FAT chains, cross-links, cycles, directory overrun, reserved/bad clusters, and
out-of-volume references. The inspector must not silently repair an image while
deciding whether it is valid. Keep data recovery outside ordinary validation.

FAT16 fixtures are mandatory here; VA guest FAT16 runtime acceptance belongs
to M19/M21/M22 as applicable. FAT32 and LFN remain excluded. Preserve existing
ASCII/8.3 behavior and do not import a codepage/NLS project into this milestone.

## 6. Device identity and DOS drive assignment

Specify the relationship among controller instance, target/LUN or native unit,
physical device, partition/volume, kernel block-device unit, and DOS drive letter.
Record actual numeric conventions from the pinned source instead of guessing
that every layer uses the same index or begins at zero.

Define deterministic enumeration for the selected profiles and record the
intended first HDD letter under the accepted new M16 floppy configuration.
Preserve physical FDD1/A: and FDD2/B: identities and their qualified profiles.
A reserved letter alone is not evidence of the new M16's B: acceptance. If that
prerequisite is missing, report the actual gap instead of silently renumbering
floppies or treating B: as deferred again.

Address absent devices, empty/removable media where already relevant, multiple
supported volumes, invalid/unsupported partitions, and rediscovery/reset. State
when a letter is assigned, retained, skipped, or unavailable and why. Protect
the identity of in-flight requests and cached data; media revalidation must not
retarget a pending write to another volume.

Define boot-device identity separately from current/default DOS drive. For
M19/SCSI data milestones the system boots from the accepted existing source;
M20 later establishes SASI boot and its drive mapping. Do not assume one drive
letter identifies the same physical device in every boot arrangement.

If more than one consistent assignment is possible, choose and document a
backward-compatible policy using the current kernel/loader contract. Routine
policy selection within this scope does not require another approval. Consult
only if it conflicts with an accepted behavior or needs a broader design change.

## 7. Executable profiles and reproducible fixture generation

Implement or extend the existing versioned schema/manifest format to encode
the selected contracts. Include identity/revision, transport/controller family,
container and payload mapping, device capacity/block units, partition and
filesystem profile, conversion rules, limits, validation policy, planned target
milestone, provenance, and current qualification level. Encode the deployment
kind, controller owner, permitted boot sources, initialization prerequisite,
and external-driver ABI reference without conflating them with media format.

Validate cross-field invariants, not only JSON types. Reject ambiguous implicit
units and contradictory profile fields. Keep these statuses distinct:

- Specified and host-validated by M17.
- Planned for a named runtime milestone.
- Actually guest-qualified by an identified revision and run.

Inspect public/private disclosure constraints before placing concrete profile
values in a public schema or fixture. Do not leak private facts merely by
encoding them as a test constant or image header.

### 7.1. Generator requirements

Reuse the project's media construction tools where they provide the right
contract. Extend them rather than making a competing all-purpose disk builder.
Create only new disposable synthetic outputs at explicit destinations; refuse
to clobber original/private media. Output generation is not authorization to
repartition or format a user's live disk.

Use original synthetic contents, deterministic labels/serials/timestamps under
the established reproducible-build policy, explicit byte order, and checked
layout arithmetic. Generate images with:

- A legal FAT12 baseline or reused qualified FAT12 fixture.
- A clearly valid FAT16 data volume for each selected initial HDD profile,
  sharing payload data where the contracts permit.
- A nonzero partition/payload offset case that detects omitted or double-added
  offsets, rather than only an easy unpartitioned zero-offset volume.
- Distinguishing files, a subdirectory, boundary-crossing data, and sentinels
  that support later reads/writes and non-target preservation checks.
- Named pristine input and expected-result metadata for later controlled
  mutation, without shipping precomputed successful guest output as a test.

Choose practical small fixtures that genuinely classify as FAT16. Do not label
an undersized FAT12 volume FAT16, create huge images just to test integer limits,
or rely on host filesystem nondeterminism. Use arithmetic/model tests for limits
that need not allocate a correspondingly large backing file.

Keep physical sector, partition, and FAT assumptions independently adjustable
within the validated profiles. A single monolithic blob with undocumented magic
offsets is not a reusable test fixture. Record generation command, tool/source
revision, profile identity, full file size/hash, and expected structure/content.

Generate required canonical fixtures twice from clean outputs and compare bytes.
Use the existing clean-build/environment policy where applicable. If a format
contains intentionally variable fields, normalize them by an explicit contract
before calling the resulting fixture reproducible; do not simply ignore
unexpected differences.

### 7.2. Inspector requirements

Provide a read-only command that reports format/profile, container/payload
bounds, capacity and units, partition/volume layout, BPB/FAT classification,
required structural checks, and file/data identities needed by later tests.
Use stable machine-readable output plus a concise human summary if consistent
with existing tooling. Verify inspection leaves input bytes unchanged.

The inspector must independently verify the generator's output. It may share
well-reviewed schema or basic decoding helpers, but it must not merely repeat
the generator's success flag or use the same unchecked layout calculation as
its only oracle. Use an independent existing FAT tool where compatible, manual
expected arithmetic for selected fixtures, or a separately reasoned parser and
negative tests. Do not require a tool that assumes 512-byte sectors for a
different selected profile and silently discard its errors.

Expose at least valid-supported, valid-but-unsupported, malformed/truncated,
and inconsistent outcomes with documented non-success behavior. Unsupported
media must not trigger repair, automatic format conversion, or a fallback that
interprets unknown bytes as a writable default profile.

## 8. Boundary and negative test matrix

Derive cases from the selected actual profiles. Each case records its contract,
construction/mutation, expected classification/result, actual output, and
candidate/tool identity. Retain original input hashes and ensure read-only
operations do not modify them.

| Area | Required representative cases |
| --- | --- |
| Container | Correct signature/header and payload extent; truncated header/payload; inconsistent capacity; unsupported recognized variant |
| Addressing | First/last legal block, exact end versus beyond end, zero-count contract, overflow in start/count/byte conversion |
| Sector translation | Selected equal/unequal unit sizes, nonzero offsets, alignment requirements, and explicit unsupported ratios |
| Partition | Valid supported layout, missing/invalid entry, overlap, outside-device range, bad start/length units, reserved-area collision |
| BPB/layout | Legal FAT12/FAT16, wrong sector/cluster sizes, conflicting extent fields, insufficient FAT capacity, metadata beyond volume |
| FAT boundaries | Cases around the documented FAT-type transitions and selected capacity limits, with expected classification independently justified |
| Files/chains | Known bytes, subdirectory and boundary-crossing files, truncated/cyclic/cross-linked chains, invalid cluster references, required FAT-copy differences |
| Mapping | Stable device/partition/drive identity model, absent/unsupported entries, and no accidental aliasing or boot-drive assumptions |
| Deployment | Reject profiles that require SCSI boot, depend on loading the driver from an unavailable SCSI volume, or assign two owners to one controller; contract/schema tests only |
| Reproducibility | Clean regeneration gives the required identical bytes/manifests; seed/time/environment are explicit |
| Preservation | Inspector and malformed/unsupported probes leave source files untouched; output creation does not clobber controls |

Use deliberate mutations of valid disposable fixtures so each rejection has
one identifiable cause. Do not make an ambiguous pile of corruptions and count
any error as proof of a particular invariant. Existing tested validators may
be reused with their version and supported geometry recorded.

For FAT thresholds and maximum sizes, use documented values from the active
contracts/specifications and checked formulas. Do not bake remembered constants
into both generator and validator without checking their meaning and units.
Do not claim guest behavior from host-only boundary tests.

The common request/conversion model may be tested using a pure simulated byte
store to detect wrong offsets and partial-count semantics. Label it as a model
test. It does not constitute VAEG SASI/SCSI device operation, DOS mounting,
guest file writes, or boot acceptance.

## 9. M17 acceptance and existing-path regression

| Gate | Required evidence |
| --- | --- |
| M17-ROUTING | Earlier storage-M16 supersession preserved; current M16/M17 status, inserted M18 and shifted M19-M32 dependencies agree; history is preserved |
| M17-BASE | Actual new M16 baseline/status and current source, memory, and tool identities are recorded without invented PASS |
| M17-CONTROLLERS | Evidenced SASI and SCSI interfaces and ownership boundaries with no invented hardware equivalence |
| M17-DRIVER-CONTRACT | External SCSI .SYS decision, built-in FDD/SASI boot boundary, source-linked VA loading/ABI/registration audit, and concrete M21 gap/test handoff; no untested runtime claim |
| M17-UNITS | Capacity, device/partition/DOS/byte units, checked conversions, and limits are unambiguous |
| M17-FORMATS | Concrete initial SASI and SCSI HDD profiles, supported/unsupported inventory, and versioned decisions |
| M17-PARTITIONS | Selected partition/BPB/reserved-area rules and later SASI-boot compatibility constraints are resolved |
| M17-DRIVES | Explicit deterministic device/volume/unit/drive and boot-identity policy |
| M17-SCHEMA | Machine-readable profiles and cross-field validation agree with the written contract |
| M17-FIXTURES | Original reproducible FAT12/FAT16 fixture set with hashes, generation commands, and known expected content |
| M17-INSPECTOR | Independent read-only structural/content inspection and correct unsupported/malformed distinctions |
| M17-BOUNDARIES | Positive, conversion, capacity, classification, corruption, and input-preservation tests pass |
| M17-REGRESS | Existing accepted paths remain consistent; applicable changed-tool/common-code regressions and CI pass |
| M17-HANDOFF | Concrete M19 SASI and M21 external-SCSI inputs, contracts, named implementation gaps, exact artifacts, revisions, and CI agree |

Mandatory profile facts and tests cannot be converted to UNKNOWN/NOT_RUN just
to complete the milestone. Optional later capabilities may remain explicitly
deferred. Use consultation when a mandatory choice cannot be resolved from
available evidence. Do not fabricate hardware behavior to fill the table.

M17 normally leaves production guest code and boot artifacts unchanged. Reuse
the identified accepted M16 control and its valid evidence when source/config
identity is unchanged. If a scoped tool/packaging/shared-code change affects
the existing boot image or runtime path, rebuild and run the affected normal
M16 regression and record the new identity. Do not perform unrelated broad
guest repairs just to make a contract task look like a runtime milestone.

Run focused checks during iteration and the required complete gates for changed
components at closure. Verify source/tree and final CI identities. Do not
report a full M16 retest when only fixture tools ran, or demand a fresh D88 build
solely to rename unchanged accepted bytes M17.

## 10. Privacy, work discipline, publication, and CI

Use a persistent excluded private root such as
`$HOME/work/pc88va/freedos-pc88va/.private-evidence/m17/`.
Keep detailed hardware/document locators, private profile facts, original
ROM/media identities, analysis, traces, snapshots, and concise progress there.
Do not overwrite historical storage evidence labelled m16 or evidence for the
new M16 floppy/input task. Preserve its original identity and migration link.

Bounded read-only analysis of local documents, ROMs, and OS media is allowed
when necessary to resolve an interface. Preserve original bytes. Do not copy
private boot sectors or partition tables into public fixtures, or publish
private-derived concrete values through tests, filenames, logs, or code.
Use public/synthetic inputs in public CI and retain the established promotion
policy. Preserve root GPL-2.0-or-later and third-party/component licenses.

When a required public implementation/profile would disclose a private-only
fact, finish the concrete local result, identify the exact disclosure decision,
and continue independent work. Do not silently publish it, or claim complete
published support with a mandatory profile withheld and unexplained.

Use finite run/output bounds, checked command exit statuses, and identifiable
stop reasons. Do not reuse stale generated media/manifests after a failed step.
Avoid giant repeated traces for questions that source inspection and a small
layout test can answer. Keep toolchain/dependency pins stable.

After local acceptance and scoped diff/privacy review:

1. Commit task-owned child/tool changes in their source-of-record repositories.
2. Push child topic branches normally before publishing parent gitlinks.
3. Update parent contracts, profiles, routing/status, manifests, and handoff.
4. Commit/push the parent topic and run applicable public CI.
5. Verify the result belongs to the actual final behavioral revision or an
   explicitly allowed equivalent documentation-only revision.

Fix real CI failures and continue; record transient service failures before
justified retry. Do not weaken validation, refresh unexplained goldens, or
replace a failing dependency pin to obtain green checks. Avoid self-referential
report-commit loops: place final published tip/CI identities in the durable
local handoff or use the repository's equivalent established mechanism.

## 11. Artifacts and concrete M18/M19/M21 starting points

Deliver the contract/ADR, machine-readable profiles, source-controlled fixture
generator/inspector/tests, reproducible permitted synthetic fixtures, and a
manifest linking sources, profiles, commands, sizes, full SHA-256, results, and
qualification level. Use the actual image extensions for the chosen formats;
do not call an HDD image D88 unless it really has that format.

Use a durable local handoff directory such as
`$HOME/work/pc88va/freedos-pc88va/.private-evidence/m17/handoff/`.
Provide uniquely named fixture bundles/manifests, a usage README, and
`M17-final-handoff-<candidate-id>.md`. Preserve pristine inputs and deliberate
invalid examples as separate roles so they cannot be mistaken for normal media.

Include the unchanged accepted boot D88 identity/path or, if this task actually
changed and requalified it, the exact tested replacement. Do not manufacture a
new boot artifact requirement or associate synthetic FAT16 validation with an
untested guest image. Copy deliverable bytes exactly and compare size/hash.

For new M18, provide the source-linked device initialization/resident-end,
request/buffer ownership and supported-memory contracts already audited here.
These are inputs to its memory accounting, not a requirement to implement its
memory repairs, utility ports or assembler qualification within M17. Follow
`docs/tasks/M18-memory-layout-basic-disk-goal-Codex.md` for the separate compact
M18 goal; full upstream distribution/Japanese support is not its requirement.
M18 needs M16/M17 baseline closure;
M19 implementation starts after the new M18 baseline is qualified.

The M19 handoff must specify:

- Exact source/configuration baseline and the selected SASI controller/profile.
- Chosen guest integration boundary and existing routines to extend.
- Capacity/unit/partition/BPB/drive contracts, with versioned profile identities.
- Pristine synthetic media, known files/offset expectations, and inspector commands.
- The first distinguishing device-read test and the subsequent planned
  filesystem/write/error tests, clearly labelled NOT RUN under M17.
- Data-write protection, timeout/retry, partial-count, and persistence rules.
- Constraints to preserve for M20 SASI boot and separate SCSI data milestones.
- Remaining optional/excluded formats and any concrete external decisions.

The M21 handoff must additionally specify the external driver's planned source
and packaging location, supported `DEVICE=` startup sequence, source-linked ABI
and unit-registration contracts, bounded kernel integration gaps, single-owner
rules, resident-memory budget, and the actual read-only acceptance workload.
State which boot sources depend on M20 qualification. Include unchanged-media,
no-driver/no-device, failed-initialization, unsupported-media, and write-rejection
cases. Keep M22 write and M31/M32 MO requirements separate and pending.

The final response must list actual changed files, decisions, tested host
commands/results, applicable baseline regression, artifact paths/sizes/hashes,
commit/CI identities, and remaining limits. Clearly state that M17 qualifies
contracts/fixtures, not SASI/SCSI DOS runtime or HDD boot. Hardware remains
NOT RUN or DEFERRED HARDWARE VALIDATION unless actual evidence exists.

## 12. Progress, consultation, and task persistence

Update persistent progress after meaningful decisions, experiments, or repairs:
baseline/candidate identity, settled contracts with evidence, first unresolved
boundary, hypothesis, next distinguishing action, completed/remaining gates,
fixture/tool identities, source snapshot, and reproduction commands.

Report normally during work and save/present a checkpoint every 30 minutes of
active work. State new discriminating evidence or validated work, the current
blocker, next action, acceptance progress, and latest tested artifacts. Mark
pending builds/CI honestly. Reporting does not pause the task or promise a
background timer after the active session ends.

Prepare/update private `M17-consult-current.md` when:

- 60 minutes of active investigation yields no new discriminating evidence,
  resolved contract uncertainty, or validated repair for the current blocker;
- two evidence-supported repair attempts leave the same failure unexplained;
- the next proposal changes the accepted architecture, memory/loader ownership,
  user-visible compatibility, or mandatory scope;
- documentary, source, emitted-code, and runtime observations remain contradictory.

Unchanged rebuilds, more trace volume, or relabelling a hypothesis is not progress.
A known build/CI wait is pending work. Consult earlier when the decision is
already specific enough to formulate.

The consultation contains one precise question, expected contract, last good/
first unresolved boundary, evidence, attempts and excluded hypotheses,
alternatives/tradeoffs, recommendation, artifact/source identities, reproduction
commands, and independent work that can continue. Preserve older consultations
and notify the user with a local path and short permitted summary. Do not claim
to have consulted Astra or send private material to another service silently.

Continue useful independent work while awaiting a decision; do not stack
speculative changes on the disputed path. If evidence resolves it within the
accepted design, record that resolution, notify the user, and continue without
renewed permission. Do not repeatedly ask the same unchanged question.

## 13. Completion and justified interruption

Report `M17 PASS (CONTRACTS/FIXTURES)` only when the renumbered storage scope and all
applicable mandatory gates are complete, the external SCSI deployment/ABI audit
and downstream handoffs are concrete, SASI/SCSI HDD profiles are usable by the
next milestones, generation/inspection/negative tests pass,
required baseline regressions and public CI are satisfied, records agree,
intended topic pushes are complete, and exact fixture/tool/contract handoff
artifacts have been delivered.

This does not mean HDD read/write, FAT16 guest operation, SASI boot, or any
new M16 feature has passed merely by generating storage fixtures. Do not stop at
a survey, a profile full of unknowns, or a generator that has only validated itself.

A final blocked handoff is justified by an indispensable unavailable input or
access, a denied necessary action with no safe alternative, a hard execution
limit, or a genuinely unsatisfied prerequisite after independent useful work
is exhausted. Use `M17 DECISION NEEDED` for a specific unresolved contract/design
decision on which all remaining work depends. Persist the question,
recommendation/alternatives, exact restart state, and next command. An ordinary
unsolved defect is not an external access failure.

Finish M17 and leave new M18 and M19 onward pending. Do not rerun an already
accepted M17 solely to rename downstream handoffs. Preserve accepted new M16 features
and keep MO at M31/M32, at the end of the roadmap.
