# FreeDOS PC-88VA milestones M13-M32

Revision: 2026-09-27, compact M18 replacement. M18 covers conventional-memory cleanup, MEMMAP and a single bootable native 2HD VA basic disk with 8086-class MS-DOS 2.11-era tools and real-mode JWASMR, built by make m18-disk. Keep the already specified M13-M32 numbering: do not shift it a second time. SCSI remains external and MO remains last.

| Milestone | Scope | Required outcome | Dependencies | Implementation difficulty |
| --- | --- | --- | --- | --- |
| M13 | Resident common kernel and NECPC88VA FreeCOM, read-only session | Real interactive input/editing, DIR, TYPE, COM and MZ EXEC, return to a usable prompt, and a second command; qualified normal boot image | Accepted M11/M12 and current memory/ABI foundation | 5/5 - Very high |
| M14 | FAT12 floppy writes and media changes | Real sector and filesystem writes, close/flush and fresh-boot persistence, protection/error recovery, and no stale writes to replacement media | M13 | 4/5 - High |
| M15 | Supported DOS API QA and writable DOS session | Explicit supported/unsupported INT 21h and related-service matrix; file/directory/handle/memory/process/device/error behavior, FreeCOM COPY/REN/DEL/MD/RD, redirection and batch, clock and guest floppy system transfer | M14 | 4/5 - High |
| M16 | VAEG 2D support, floppy formats, physical B: and native console input | Mandatory production VAEG 2D 320/360 implementation and synthetic FDC/media tests, followed by guest qualification with the exact new build; 2D 320/360 KiB, 2DD 640/720 KiB and documented 2HC reads/writes on A: and physical FDD2/B:; media change and cross-drive copy; VA cursor keys/display coherence; VA and VA2 guest-timed key repeat and native function keys | Actual M15 baseline; VAEG 2D path before dependent guest tests; per-model evidence and matched emulator/guest revisions | 4/5 - High |
| M17 | Common storage contracts and media formats | Built-in FDD/SASI and external SCSI ownership; source audit of VA DEVICE=/INIT/block-unit registration; concrete capacity/sector/partition/BPB/drive contracts; reproducible FAT12/FAT16 fixtures and independent validation; M18 memory/device-residency input plus M19/M21 storage handoffs | Actual new M16 baseline; independent host work may proceed while a runtime prerequisite is unresolved | 3/5 - Medium |
| M18 | Conventional-memory cleanup and one bootable 2HD VA basic disk | Account for native RAM/resident/MCB ownership, repair proven stale reservations or avoidable fragmentation, and validate allocation/EXEC; MEMMAP plus selected basic shell/editor/floppy tools and real-mode JWASMR; all mandatory tools on one 2HD disk with measured working space; guest edit/assemble/COM-and-MZ-run on A: with B: empty; isolated public-input-only make m18-disk and one exact tested D88/sources/licenses/manifests | Actual M16/M17 baseline, accepted native memory/toolchain contracts and public QA/media builder; no Japanese or complete upstream distribution requirement | 4/5 - High |
| M19 | SASI HDD as a data drive | Built-in VA storage integration, discovery and volume registration, common-kernel FAT16 reads/writes, errors/protection and persistence while booting from accepted FDD media | M18 plus M17 storage contracts; required M15 acceptance | 4/5 - High |
| M20 | Native SASI boot | Firmware-to-loader-to-kernel-to-FreeCOM boot with no bootable FDD required; correct boot-volume identity, resident I/O handoff, normal session and recovery | M19 | 5/5 - Very high |
| M21 | External SCSI .SYS and read-only HDD access | Normal DEVICE= loading from an accessible FDD/SASI volume; actual INIT, resident memory and DOS unit/BPB registration; controller/discovery/partition reads and FAT16 files through the common kernel; write rejection, unchanged media, bounded failures and no-device behavior | M17 driver/media contracts and M15 foundation; M20 for SASI-boot qualification; follows M20 in the default sequence | 4/5 - High |
| M22 | SCSI HDD writes through the same .SYS | Controlled file/directory/FAT updates, close/flush and reopen/fresh-boot persistence; protection, non-target preservation, truthful partial results and bounded failure recovery | M21 | 4/5 - High |
| M23 | Integrated FDD/SASI/SCSI storage release | Reproducible supported combinations, FDD and SASI boot, stable drive mapping, cross-drive operations, SCSI-driver omitted/loaded-without-target cases, memory regression, versioned driver packaging and exact qualified artifacts | M15-M22 | 3/5 - Medium |
| M24 | Japanese output and NLS | Qualified character/codepage contract and Japanese display through the accepted VA console; NLS data/services and DBCS boundaries, with ASCII behavior preserved | M23 | 4/5 - High |
| M25 | Japanese input | Agreed Japanese input method and real shell delivery, editing and control-key behavior with correct DBCS boundaries; record the actual supported method | M24 | 4/5 - High |
| M26 | Japanese 8.3 filenames | Correct supported CP932/DBCS short-name parsing, search, wildcard and directory operations through DOS/FreeCOM; byte boundaries and compatibility/error tests | M24/M25 | 4/5 - High |
| M27 | LFN feasibility and implementation contract | Inspect available implementation/license options; measure code, resident memory and conversion-data costs on VA; define API/encoding/on-disk ownership, short-name compatibility and an evidence-based GO/NO-GO decision | M23/M26 | 3/5 - Medium |
| M28 | ASCII LFN read support | Under an M27 GO decision, read and enumerate valid supported long names through the selected DOS interface; retain 8.3 aliases and safely reject malformed/unsupported sequences | M27 GO | 4/5 - High |
| M29 | ASCII LFN updates | Under the selected LFN design, create/rename/delete long-name entries with collision-safe short aliases, consistent directories, persistence and defined failure behavior | M28 | 5/5 - Very high |
| M30 | CP932 LFN and language release | Qualified CP932/Unicode conversion for the selected supported repertoire, measured memory/table strategy, Japanese long-name operations and complete ASCII/8.3 regression | M26/M29 and the M27 conversion contract | 5/5 - Very high |
| M31 | MO reads and medium reidentification | Extend the external SCSI architecture for the selected MO profiles; no-medium/insert/change detection, capacity/block-size revalidation, stale-cache invalidation and real file reads without changing media | M22/M23; follows disposition of M24-M30; MO remains the final extension | 4/5 - High |
| M32 | MO writes, safe exchange and final integration | Writes and persistence on disposable MO media; write protection, flush/error behavior, safe exchange, no writes to the wrong replacement medium, and full accepted-storage regression and handoff | M31 and accepted earlier features | 5/5 - Very high |

## Interpretation and scope

This is the updated implementation plan, not a completion report. Preserve the
new M13-M32 numbering and the repository's actual evidence/status records.
The earlier M16 insertion was a separate migration. The immediately preceding
M18-M31 -> M19-M32 mapping inserts the memory/basic-disk M18 exactly once.
If active records already use M13-M32, change M18's content in place; do not
introduce M33. If they still use the preceding M13-M31 plan, apply that single
mapping. M13-M17 retain their meanings and actual status. This revision replaces
the earlier broad M18 English-distribution scope, not another milestone number.
Historical evidence keeps its number and identity with an explicit cross-reference.
A previous storage M16 PASS is not a new floppy/input M16 PASS.

The difficulty scores are engineering estimates for this revision, not elapsed
time estimates or proof that a milestone has passed. M13 and M20 combine several
boot/runtime boundaries. M18 is reduced from the earlier 5/5 broad distribution
to 4/5: the selected payload is smaller and Japanese/fullscreen editor/full-package
work is deferred, but memory lifetime repairs and guest assembler memory needs
remain significant unknowns. The score is not a promise that M18 will be easy; new M16 includes required implementation in both VAEG
and FreeDOS plus input integration, while M17 is narrower contract/tool work. External-driver integration adds work to M21
but gives SCSI a clear deployment and ownership
boundary.

M15 is comprehensive within an explicitly selected DOS API contract. It does
not promise every historical DOS function, undocumented behavior, IBM-PC BIOS
interface or existing DOS application's compatibility. Unsupported services
need defined results. Later storage milestones add tests for their new devices
and paths without silently expanding or weakening M15's accepted contract.

Use the common kernel's FAT12/FAT16 implementation. FAT12 remains the floppy
baseline; FAT16 is the initial HDD objective, subject to the concrete M17 media
profiles and measured limits. M17 host-valid media are not evidence of guest
FAT16 support. FAT32 is outside this plan.

## Adopted SCSI architecture

The deployment decision is settled: SCSI is an optional external DOS block-device
`.SYS`, loaded using `DEVICE=` in the supported CONFIG.SYS/FDCONFIG.SYS path.
The driver's selected 8.3 filename and options are decided from the actual build
and packaging conventions in M17; this document does not claim an existing
binary with a particular name.

Boot from an accepted FDD or SASI source, load the driver from an already
accessible volume, initialize its units, and then use SCSI volumes through DOS.
Do not place the sole driver copy on the initially inaccessible SCSI disk.
The current configuration has no assumed SCSI boot service. SCSI firmware boot,
a new SCSI boot loader, and an IBM-compatible disk BIOS shim are outside scope.
Reading programs from SCSI after initialization is data-drive use, not native
SCSI boot.

Keep INT 21h file services, FAT and directory management in the common kernel.
The external driver owns controller/discovery/capacity handling, the selected
partition/volume mapping, unit/BPB presentation, block transfers and transport
error reporting through the actual DOS device interface. It must not create a
parallel filesystem or use emulator host-file access as guest storage.

Keep the FDD/SASI boot-access path in the loader and native kernel integration.
M19 prepares resident SASI access and M20 proves the early boot path and handoff.
Share source helpers where useful without forcing SASI and SCSI to have the
same binary deployment or hardware assumptions.

Start with one SCSI driver binary, separating controller and disk/volume code
internally. A separate ASPI manager and disk driver are not requirements.
Each controller has one active owner; avoid duplicate kernel/external scans or
competing HDD and MO drivers. M31/M32 can extend the same architecture and reuse
its transport; a separate MO binary is not a prerequisite.

External loading is configuration-time initialization, not a promise of hot
loading, safe unloading or automatic memory savings after loading. Measure
resident code/data, retained buffers, stack needs and initialization-only memory
on the actual supported VA memory configurations. Do not import a 640 KiB or
DEVICEHIGH/UMB assumption merely from IBM-PC FreeDOS documentation.

## M17 and M21 responsibility boundary

M17 must inspect the actual pinned VA kernel's configuration-file processing,
driver headers and entry points, request ABI, INIT return/resident-end semantics,
unit counts/BPB pointers, device-chain/DPB registration and drive allocation.
Document the source facts, existing runtime evidence, unverified paths and
bounded repairs required for M21. General upstream FreeDOS support and an M15
API PASS do not prove VA external block-driver acceptance.

M17 does not implement the operational SCSI driver or require a prototype to
claim contracts/fixtures completion. M21 implements the driver, performs the
identified bounded loader/registration repairs, and demonstrates real `DEVICE=`
loading and read-only files through the normal kernel/FreeCOM path. M22 qualifies
writes. A broad redesign requires the existing consultation process; routine
bounded implementation within the agreed architecture does not need renewed
permission.

M21 acceptance includes normal startup without private diagnostic helpers,
omitted-driver and absent-device behavior, failed initialization without phantom
drives, malformed/unsupported media, write rejection and unchanged input hashes,
stable mapping, bounded errors and actual resident-memory measurements. M22 adds
persistence and non-target preservation; M23 qualifies the supported combinations.

## Japanese, LFN and MO sequencing

Retain the previously agreed Japanese output/NLS, input, Japanese 8.3 and staged
LFN sequence. Japanese input does not implicitly authorize writing an entirely
new general-purpose conversion engine. Qualify the selected input method and
its source/license dependencies under the existing contract.

LFN is conditional on M27's measured feasibility decision. CP932 LFN is a bounded
encoding target, not a promise of universal Unicode input/display. M27 must
compare available code and conversion-table strategies, including disk-backed
or compact data where appropriate, and establish their memory/I/O and licensing
costs. Do not conclude either feasibility or impossibility from the mere need
for Unicode conversion, and do not promise a full table resident in RAM.

If M27 establishes NO-GO, record M28-M30 as deferred/not implemented with the
specific reasons; never relabel them PASS. That decision does not remove the
separately agreed MO objective. Continue to M31/M32 after the intervening work
has a clear disposition. Keep MO at the end and retain its existing numbering.
Safe MO exchange includes drive identity and pending-write/cache ownership;
successful reads alone do not qualify safe removal or writes.

## New M16 scope and existing work

The user reports that real VA hardware supports 2D but current VAEG does not.
Implementing VAEG 2D support is therefore mandatory M16 scope, with an isolated
VAEG topic worktree, actual image/drive/FDC-path fixes and meaningful synthetic
regressions. It is not an optional repair or grounds to mark 2D unsupported.
Locate the missing behavior from the real sources; do not guess geometry or
work around an emulator bug in the guest.

The dependency is production VAEG 2D support -> FreeDOS block/FAT12 support ->
normal FreeCOM read/write, cross-drive and persistence qualification. Independent
input/B: work may proceed alongside it. Require VAEG component tests and actual
DOS workload evidence, each identified separately. Deliver the matched VAEG
executable/source/build identity and tested media, plus each repository's relevant
commit/CI results. An old VAEG binary or guest-only PASS cannot close this M16.

Implement read/write data-volume support for 2D 320/360 KiB, 2DD 640/720 KiB and
2HC, plus a real second floppy drive at B:. Establish exact sector geometry,
density/stepping, BPB and container mapping per profile. Resolve 2HC from actual
VA documentation and source; do not silently replace it with another 2HD format.
Qualify both physical drives and VA/VA2, different formats concurrently, media
changes, cross-drive copying, protection/errors and persistence. Per-format
firmware boot is a separate capability, not implied by data-volume support.

The console portion covers VA cursor-key input and visible/logical cursor
coherence, VA and VA2 key auto-repeat, and all actual native function keys with
their supported modifiers and DOS/FreeCOM semantics. Use one repeat producer and
guest time; avoid dependence on or duplication of host frontend repeat events.
Preserve non-destructive peek, consuming read, release, flush and complete
extended-key events. Cursor scope is the console, not a mouse/graphics project.

These features are active M16 work, superseding the earlier deferred-backlog
instruction. Preserve earlier implementations and qualify them against the new
scope rather than restarting blindly. Early boot progress messages alone remain
separate because they were not re-added in the current request. No new milestone
number is assigned to that remaining item.

## Revised M18 memory and compact basic-disk scope

Account for native RAM, hardware reservations, loader/kernel/device residency,
initialization lifetime, MCBs, PSPs/environments, FreeCOM and observer footprint.
Investigate the reported conventional-memory remnants/fragmentation before
reclamation. Do not merge through live allocations, assume IBM-PC 640-KiB bounds,
or fake free-memory reports. Compare total free and largest usable block at
matched stages; verify real allocation/free/resize and COM/MZ EXEC. Preserve
accepted capacities, explain remaining reservations and fix proven defects.

Use a compact MS-DOS 2.11-era *tool scope*, retaining the common FreeDOS kernel
and VA FreeCOM and their newer supported DOS services. This is not a DOS 2.11 API
downgrade or redistribution of Microsoft/NEC DOS. Required payload: existing
shell file/directory/batch/redirection commands, EDLIN, MORE, CHKDSK, FORMAT,
SYS, MEMMAP and JWASMR, with original small assembly examples and English help.
The user's `jasmr` is interpreted as JWASMR.EXE, JWasm's DOS real-mode assembler;
confirm against existing project notes. It must run on VA and assemble COM and
MZ examples which then execute and return normally. Preserve the DOS services
it needs; do not substitute the protected-mode build or a host-only assembler.

Ship 8086-class ASCII tools and 8.3 names with measured RAM requirements and
qualified VA I/O. Japanese/NLS/DBCS/LFN remain later work. EDLIN is deliberately
the small editor; full-screen EDIT, FreeDOS Floppy Edition/BASE package parity,
standard MEM, a C compiler and a separate linker are not M18 requirements.
FIND/SORT/DISKCOPY/DISKCOMP/FC/COMP/MEM/DEBUG are optional if cheaply qualified;
they must not hold up the required compact set. MEMMAP provides safe MCB mapping,
owner/size/free/largest-block information, /CHECK and DOS stdout redirection.

`make m18-disk` orchestrates isolated source/component/image builds with separate
build/m18 and dist/m18 outputs; it preserves QA disks and other worktrees.
Produce exactly one bootable native 2HD D88 containing every mandatory tool;
no supplemental tools disk is allowed. Record the accepted 2HD geometry and a
cluster/file capacity budget, including measured space for editing/assembly on
a writable copy on A: with B: empty. Remove optional payload first; unresolved
mandatory-payload overflow requires consultation, not a silent second disk.
Provide corresponding sources, licenses, pins, hashes and reproduction guides
as host-side companion files. Keep QA/data-test images separate from the normal
one-disk output; their use must not become a dependency for ordinary operation.
No private ROM/docs/D88 template or historical trace tree may be a public build
input. Qualify the exact public disk bytes privately under the matched VAEG/ROM
setup; public build success alone is not guest PASS.

The authoritative detailed goal is
`docs/tasks/M18-memory-layout-basic-disk-goal-Codex.md`.
It supersedes the broad `M18-memory-layout-english-distribution-goal-Codex.md`;
retire that active path with a supersession link. Do not use both as cumulative
requirements. No XMS/EMS/UMB, IBM memory BIOS shim, SASI/SCSI, Japanese/LFN or MO
implementation is added to M18. Keep the existing later objectives.

## Applying this revision

Update the active repository's canonical milestone table/routing and handoff with
these M13-M32 rows, preserving M00-M12 and actual implementation status. Avoid two
competing active roadmaps. Place this file at
`docs/freedos-pc88va-milestones-M13-M32.md` if a separate roadmap is used, and
reference it from the canonical entry point. Retire the previous active M13-M31
filename with a redirect/mapping; historical reports retain their old identifiers.

Current task files are:

- `docs/tasks/M16-floppy-formats-console-input-goal-Codex.md`;
- `docs/tasks/M17-storage-contracts-media-formats-goal-Codex.md`;
- `docs/tasks/M18-memory-layout-basic-disk-goal-Codex.md`.

Preserve the earlier supersession of the old storage-M16 goal by the current M17.
Do not rerun accepted M16/M17 work merely to update future routing. New M18 is
not considered accepted by the renumbering or by an old SASI report named M18.
Update future task links/dependencies once and retain historical evidence paths.

The host is ryzen (Ubuntu 24.04 amd64), with the common root
`$HOME/work/pc88va/` on that host. The FreeDOS, VAEG and private-document siblings
are `freedos-pc88va/`, `vaeg/` and `pc88va-private-docs/`. Resolve actual absolute
paths/worktrees and retain the accepted toolchain; old Mac paths are historical.
These supplied documents do not mean either host's checkout was edited, that
any milestone was executed, or that commits/CI have already completed.

Continue the requested milestone using its own goal. The roadmap does not
turn an M16/M17/M18 goal into permission to implement all later milestones.
Preserve the established private/public evidence policy, native memory contracts,
30-minute checkpoints and stagnation/consultation rules. VAEG evidence must remain
distinct from optional hardware validation. Historical trace bulk is not a
mandatory migration/restart input; retain the selected necessary resume state.
