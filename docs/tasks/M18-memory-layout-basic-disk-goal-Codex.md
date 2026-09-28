# M18 goal: conventional memory and a compact PC-88VA basic disk

Revision: 2026-09-28. Start from the integrated parent main commit identified by
the user as `d81bba18...`. The practical distribution remains exactly one
bootable 2HD floppy.
Repository placement: `docs/tasks/M18-memory-layout-basic-disk-goal-Codex.md`
in the active FreeDOS task worktree on `ryzen`.

## 0. Goal, authority and numbering

Complete M18 with these outcomes:

1. Account for VA conventional memory and resolve demonstrated stale reservations,
   lifetime defects and avoidable MCB fragmentation without reclaiming live storage.
2. Deliver exactly one bootable native 2HD normal-use FreeDOS disk with an
   MS-DOS 2.11-era *tool scope*,
   an editor, a real-mode assembler and a memory-map command. Keep the accepted
   common FreeDOS kernel and NECPC88VA FreeCOM and their supported DOS services.
3. Implement the exact `make m18-disk` target, with isolated builds and a complete
   public-redistributable disk/source/license bundle distinct from the QA disk.

This replaces the earlier broad M18 English-distribution goal. Do not require
FreeDOS Floppy Edition package parity, a full upstream BASE installation, a new
fullscreen editor, or Japanese/NLS/DBCS support. The selected payload in section 6
is the acceptance floor; optional tools do not become new blocking gates.
"MS-DOS 2.11-era" describes a compact command set and workflow, not an API ceiling,
strict historical emulation, a version lie, or permission to redistribute
Microsoft/NEC DOS binaries, boot sectors or utilities. Do not downgrade FreeDOS
or change its version reporting to 2.11 to satisfy this description.

The user's `jasmr` is interpreted here as `JWASMR.EXE`, the DOS real-mode version
of JWasm. Treat this identification as an explicit working assumption. Verify
it against existing project notes before selecting a pinned source. If those
notes identify a different program, raise that specific discrepancy; otherwise
proceed with JWASMR without a new approval round. Do not substitute a similarly
named unrelated package or a 32-bit protected-mode assembler.

The user reports that M16/M17 have made the system usable and suspects unusable
remnants in conventional memory. Inspect actual acceptance records and treat
the suspected cause as a hypothesis, not proof that an allocation is dead.

The insertion of M18 has already been specified: immediately previous M18-M31
become M19-M32 exactly once. If active records already use M13-M32, replace only
the M18 scope; do not shift them again or invent M33. If records still use the
preceding M13-M31 plan, apply that single mapping. Preserve M13-M17 and all
historical report identifiers, hashes and statuses. Current M19/M20 are SASI
data/boot, M21/M22 external SCSI reads/writes, M23 storage integration,
M24-M30 Japanese/LFN, and M31/M32 MO. MO remains last and SCSI boot excluded.
Retire the old active `M18-memory-layout-english-distribution-goal-Codex.md`
with a short supersession link to this file; preserve its history without two
competing active M18 goals.

Authorized work includes source/dependency inspection, scoped kernel, loader,
FreeCOM, utility and build repairs, clean builds, original tests, private VA
qualification, public/synthetic CI, records, normal scoped topic commits/pushes
and a release-ready local public bundle. Continue without asking again for
routine implementation choices. Do not stop after the first diagnostic finding.

Do not start later storage/language milestones, add a general IBM BIOS layer or
XMS/EMS/UMB, reset other worktrees, rewrite shared history or merge shared main.
A public-ready local bundle is required; posting a release is not part of this
goal. Code, comments, developer documentation, help and disk text use English
ASCII. Existing native VA/V30 platform requirements remain intact.

## 1. Environment and preservation

### 1.1. Required integrated-main baseline

The user explicitly selected the integrated parent repository `main` commit
whose supplied SHA prefix is `d81bba18` as the starting point for M18. This
replaces the earlier generic instruction to select an M16/M17 task baseline.
The full SHA has not been supplied here; resolve it from the actual repository
and record it. The ellipsis is prose, not part of a Git revision argument.

Before implementation:

1. Identify the intended FreeDOS parent repository and its authoritative main
   remote/tracking ref. Resolve `d81bba18` to exactly one commit object; verify
   that it belongs to the integrated main history. Fetch the intended remote
   normally if necessary, without resetting a worktree or changing shared main.
   Record the full baseline SHA, relevant main ref/tip and the M16/M17 acceptance
   records associated with this integrated state. A short prefix alone is not
   a completed identity check.
2. Create an isolated M18 topic branch/worktree from that exact resolved commit.
   Do not silently substitute the current main tip if it has advanced, or an
   older M16/M17 topic tip. Keep existing checkouts and dirty changes intact.
   On resumption, reuse an existing M18 worktree descended from this baseline
   after checking its recorded source identity; do not restart completed work.
3. Resolve component gitlinks, locks, toolchain and required VAEG/control-image
   identities from this baseline and its accepted records. Check out task-owned
   component worktrees at those pins before scoped changes. Do not update a
   component to its latest branch tip merely because parent main was integrated.
4. Preserve any earlier unmerged M18 work separately. If it is needed, review
   and port its scoped changes onto the selected baseline with explicit source
   provenance and affected validation. Do not merge an unrelated old task tree
   wholesale, drop dirty fixes or reset another user's worktree.
5. If the prefix is absent/ambiguous after available normal retrieval, or cannot
   be reconciled with the intended main history, report that exact discrepancy
   with candidate identities. Do not invent the full SHA or choose a different
   baseline silently. An unambiguous verified prefix needs no renewed permission.

The user reports integration; actual acceptance and source relationships still
need inspection. Reuse valid M16/M17 evidence tied to this integrated state;
rerun affected checks for a concrete change or evidence gap, not the whole prior
project merely to begin M18. All subsequent manifests must distinguish this
fixed starting SHA from the final M18 parent/component revisions.

### 1.2. Host paths and preservation

The active host is `ryzen`, Ubuntu 24.04 amd64. Resolve its actual home directory:

| Location | Purpose |
| --- | --- |
| `$HOME/work/pc88va/freedos-pc88va/` | Parent repository; discover the actual active and component worktrees |
| `$HOME/work/pc88va/vaeg/` | Separate emulator repository; preserve unrelated changes |
| `$HOME/work/pc88va/pc88va-private-docs/` | Private hardware documents and ROM inputs |
| `$HOME/work/pc88va/toolchains/` | Host toolchains, if this convention was adopted; verify actual paths |
| `$HOME/work/pc88va/freedos-pc88va/.private-evidence/m18-memory/` | Small private progress, qualification and diagnostic evidence |

These are path conventions, not evidence of installed tools. Do not use the
old `/Users/Shared` paths as live dependencies. Read root/scoped AGENTS.md,
build/CI conventions, M16/M17 acceptance and handoffs, current memory contracts
and the accepted QA/public-media builder. Inspect `docs/msdos211-memory-compat/`
if present, including later revisions; do not substitute historical constants
from a conversation for the current sources.

Identify parent/component source revisions, gitlinks, dirty/untracked repairs,
selected ROM/model/memory configuration, known-good media, exact emulator,
kernel, packaged FreeCOM, maps and normal launch. Preserve unique source fixes
before reorganizing anything. Keep existing worktrees intact; select/create
an isolated M18 topic worktree following repository conventions.

Do not require all historical `.private-evidence/` or giant traces to be copied
from the old Mac. Retain necessary unique inputs, the last relevant control,
current progress and concise evidence; regenerate missing reproducible tests.

Determine and retain the actually accepted Open Watcom version and build
identity. Earlier project records used OW 1.9; that is a lead to verify, not a
reason to replace a subsequently qualified toolchain. An amd64 host does not
authorize switching from a pinned 1.9 build to a moving 2.0 Current-build.
If the accepted tools need an existing 32-bit compatibility environment or a
pinned container, reproduce that environment explicitly. Record host tools
separately from the 8086-class guest target and verify source/library variants.

## 2. Internal phases

| Phase | Work | Exit evidence |
| --- | --- | --- |
| M18a | Identify baseline, memory ownership and compact payload sources | Candidate identities; physical/resident/MCB/PSP map; fixed package list |
| M18b | Repair proven memory ownership/lifetime/layout defects | Accounted deltas, correct allocation/EXEC and preserved reservations |
| M18c | Build MEMMAP, selected tools and 8086 real-mode JWASMR | VA command results; guest edit/assemble/run workflow; RAM minima |
| M18d | Implement make m18-disk and public packaging | Isolated reproducible disk build and source/license manifests |
| M18e | Qualify normal disk, regression and applicable CI | Exact tested bytes, current records and complete handoff |

These are work phases, not approval gates. Independent build/package work may
continue alongside a bounded memory investigation. An inventory, printed map
or successful build alone is not M18 completion.

## 3. Establish the memory map before repairing it

Trace the actual path from native RAM-capacity discovery through loader
placement, resident kernel initialization, DOS memory arena construction,
configuration/device initialization, FreeCOM startup and child EXEC/termination.
Use source, linker maps, emitted code and bounded runtime observations together.
If accepted loader and kernel maps disagree, identify the first wrong boundary.

For the exact same model, capacity, disk contents and configuration, collect
before/after snapshots at comparable stages: end of initialization, idle normal
shell, a small child running, and after child termination. Account for the
observer program and intentional shell/environment growth.

For every relevant interval record start/end (exclusive), length, allocation
granularity, owner, purpose, lifetime, relocation constraints and source of truth.
Separate the following facts rather than summing them into one free-memory number:

- Physical RAM present and its native address/bank mapping.
- Firmware/hardware work areas, reserved regions, VRAM, ROM and unmapped holes.
- Loader scratch/staging and initialization-only code/data.
- Resident kernel, device headers/requests, buffers, stacks, vectors and tables.
- MCB headers, free/allocated/system-owned blocks and any internal DOS subblocks.
- PSPs, environments, parent/child ownership, permanent/transient FreeCOM and
  memory retained by actual resident programs.
- Alignment/padding, managed gaps, RAM outside the DOS arena, total free payload,
  largest free block, and a separately measured largest practical child.

Do not call an address range free merely because it is absent from the MCB
chain. Do not equate a system-owned block with a leak, unused-looking bytes
with dead storage, or total free bytes with maximum loadable EXE size.
Record unknown intervals explicitly and resolve every unknown that controls
the proposed reclamation. Preserve accepted native capacity detection; do not
add INT 12h/INT 15h sizing shims or assume an A0000h/640-KiB end for all machines.

Check MCB type/signature, monotonically advancing next-block arithmetic, bounds,
terminal block, paragraph counts including headers, valid owner/PSP links,
environment lifetime, chain cycles/overlap, and memory outside the advertised
arena. Treat zero-size blocks according to the actual DOS contract; do not
declare them corrupt merely because they are zero-size.

## 4. Repair memory use with ownership evidence

Investigate concrete causes such as retained initialization buffers, obsolete
loader copies, excessive permanent reservations, wrong resident-end calculations,
incorrect shell shrink/resize behavior, environment leaks, allocation-order
fragmentation, mis-sized MZ allocation fields, or incorrect free/resize/coalescing.
These are hypotheses, not a checklist of changes to apply blindly.

Use the existing common DOS allocator and native port boundaries. Make one
logical repair at a time with a before/after explanation. If releasing init
memory, prove that no vector, device chain, callback, stack, request, relocation
or saved FAR pointer still references it. Preserve interrupt and error paths,
not only the happy-path command loop. Adjacent free memory must become usable
according to the actual allocator contract; immediate eager coalescing is not
required if the allocator correctly coalesces when allocating.

Never merge across a live allocated/reserved block, compact live segments with
unknown pointers, hide an MCB, patch a memory report to print larger values, or
remove required disk buffers/stacks solely to inflate the result. Default buffer
and environment budgets may be tuned after measurement, with disk/I/O and shell
regression checks. Do not require a single contiguous free block where hardware
or necessary residency prevents one.

Required memory evidence includes:

- A byte/paragraph-accounted before/after table with actual free total, largest
  block, permanent cost, released bytes and each remaining gap's purpose.
- Actual supported INT 21h allocation/free/resize behavior (48h/49h/4Ah), boundary
  and low-memory failures, fragmentation/coalescing and owner preservation.
- Real COM and relocated MZ execution through FreeCOM and return to a usable
  prompt; a controlled near-limit allocation/EXEC probe with expected overhead.
- Repeated child execution and return to a stable post-warmup memory state,
  without unexplained monotonic loss. Distinguish normal shell retention.
- Preserved idle/input, function/repeat keys, A:/physical B:, mixed floppy
  formats, media changes, writable files and error recovery under memory pressure.

Derive the supported native capacities from the actual accepted contract, not
from an assumed IBM-PC memory menu. At minimum qualify its lowest and highest
configurations with full layout checks, and relevant capacity boundaries for
the others. Do not repeat every utility test at every capacity without a reason. Required ordinary tools must work within their stated
minimum, and smaller supported systems must fail insufficient-memory operations
cleanly. Do not silently raise an accepted minimum RAM requirement to mask a
regression or claim that a tool tested at 640 KiB works at 256 KiB.

If the suspected waste is disproved, a detailed independent accounting plus
allocation/EXEC evidence is a valid finding; inventing a byte-saving patch is
not required. Unexplained unallocatable RAM or broken lifetime/allocator behavior
is not a completed memory audit.

## 5. Include a real MEMMAP program

Ship an English `MEMMAP.COM` or `MEMMAP.EXE` (keep the command name `MEMMAP`) on
the boot disk, with buildable public source and license. Prefer an original
small utility or an appropriately licensed existing tool with a scoped VA port.
It must run as an ordinary 8086-class DOS application without debugger support,
direct IBM BIOS calls, emulator shortcuts or a hard-coded current kernel address.

Discover the first MCB through an audited supported DOS interface and the pinned
kernel's contract. A FreeDOS-specific internal structure may be used only when
its version/layout is explicitly validated and unsupported layouts fail safely.
Do not scan arbitrary memory for plausible headers. Use checked arithmetic
wide enough for physical addresses/paragraph endpoints and bound every traversal.
Known DOS suballocation details should be decoded only when their layout is
verified; otherwise identify them as system-owned, not guessed free space.

Before measuring, shrink the utility's own allocation to the code/data/stack
and bounded scratch it actually requires. A COM program that retains its initial
large allocation must not report that allocation as unexplained occupied RAM.
Keep the running stack inside the retained block and do not shrink other owners.

The normal report must include:

- MCB segment/type, owner PSP or system/free classification, safe program label
  when available, payload start/end and byte/paragraph length.
- Total managed conventional arena, free payload, largest free block, allocated
  payload, MCB overhead and the utility's own footprint, with consistent totals.
- Confirmed physical/reserved/outside-arena regions when an existing safe native
  interface supplies them; otherwise label the missing view unavailable. MCB
  enumeration alone must not pretend to be a complete physical-memory map.
- A concise validity result, precise detected anomaly and useful exit status.

Provide `MEMMAP /?` and `MEMMAP /CHECK`; plain `MEMMAP` prints a readable map.
Support DOS stdout redirection, for example `MEMMAP > B:\MEMMAP.TXT`, without
screen-only BIOS rendering. The program is observational: no automatic repair,
allocation cleanup of other processes or destructive memory probing. Document
its observation point and measurement overhead. Keep probe/stress programs on
the QA side, not in the ordinary AUTOEXEC path.

Test the parser on original synthetic valid/corrupt chains, including cycles,
out-of-range endpoints, arithmetic overflow and truncated metadata, without
deliberately corrupting a live user's arena. Independently compare guest output
with the actual kernel/loader map and DOS allocation results on the same candidate.
Porting the standard FreeDOS `MEM` command is optional. MEMMAP alone meets this
milestone's memory-display requirement. If MEM is already qualified and included,
explain differences in footprint/definitions and reconcile its results. No tool
may invent XMS/EMS support or call nonexistent IBM memory firmware.

## 6. Selected basic disk and real-mode assembler

Build a normal bootable PC-88VA FreeDOS disk for ordinary interactive use.
Preserve the accepted native loader, common kernel and fully packaged VA
FreeCOM. Do not replace them with IBM-PC release binaries or update them merely
to match the newest upstream distribution. Select pinned public sources for the
small set below, preferably reuse already qualified component versions, and
record source revision, hash, license, compiler, CPU, VA changes and tests.

### 6.1. Fixed payload

| Role | Required selection and behavior |
| --- | --- |
| Boot/shell | Native VA boot, common kernel, NECPC88VA FreeCOM; English startup/help and usable prompt |
| Files/batch | Existing supported shell DIR, TYPE, COPY, REN, DEL, MD, RD, CD, ECHO, SET, PATH, batch and redirection; verify actual aliases/options instead of adding clones |
| Small editor | FreeDOS EDLIN, qualified for ASCII load/edit/save/reopen; line-oriented editing is intentional and needs no approval to replace the earlier EDIT requirement |
| Text viewing | MORE with working DOS input/output and paging through native console services |
| Floppy maintenance | CHKDSK, FORMAT and SYS for the declared accepted native floppy profiles; filesystem checking, documented formatting behavior and bootable system transfer |
| Memory map | MEMMAP from section 5 on the boot disk; /?, /CHECK and redirected output |
| Assembler | JWASMR.EXE, rebuilt/qualified as a real-mode 8086/8088-class DOS program; guest assembly and execution, not a host-only tool |
| Starter material | Original HELLO.ASM, MZDEMO.ASM and BUILD.BAT, concise English quickstart, package/license index and safe A:/B: usage instructions |

FIND, SORT, DISKCOPY, DISKCOMP, FC/COMP, MEM and DEBUG are optional additions
only if already available or cheaply qualified under the same public/CPU/VA
conditions. Do not delay mandatory acceptance for them. Record included optional
tools and tested behavior; omit unqualified binaries. XCOPY/MOVE/REPLACE/CHOICE,
full-screen EDIT, a C toolchain, a separate linker and the remainder of the
upstream distribution are not required. JWASMR's direct output avoids making a
new guest linker another prerequisite.

CHKDSK need only expose its qualified safe checking behavior; do not enable an
untested repair mode. FORMAT must state whether it initializes the filesystem
on an already sector-formatted medium or also supports native low-level format.
Do not advertise the latter without implementation/evidence, and do not invent
new track-format support merely for this compact disk. Preserve any stronger
already accepted contract. Qualify these tools on the selected release profile;
M16's other supported data formats must retain their accepted read/write behavior,
without requiring every new utility to gain every formatting mode.

Use 8.3 filenames and ASCII text. Japanese fonts, messages, input conversion,
DBCS/NLS and LFN remain later milestones. Document this scope positively in the
quickstart as an English/ASCII basic system, not a complete Japanese DOS release.

### 6.2. CPU and native VA checks

Use an 8086/8088-class userspace build without 186/286/386-only startup/library
paths, protected mode, an FPU or mandatory XMS/EMS. Audit emitted instructions,
startup, linked runtime and actual exercised code, not just compiler flags.
Native loader/platform code can retain its documented VA/V30-specific operations.
8086 compatibility by itself does not make IBM BIOS/video/port access work on VA.
Audit direct INT 10h/13h/16h, BDA/video-memory access, timer/keyboard paths and
library defaults. Prefer existing DOS services and accepted native adapters.

Any required tool repair must remain scoped and preserve the earlier DOS ABI.
A program requiring extensive platform architecture changes triggers consultation;
do not quietly remove a required program or start a generic IBM compatibility
layer. Optional tools can simply be excluded with their reason.

### 6.3. JWASMR qualification

Use the real-mode build, not JWASMD or a renamed host executable. Upstream
JWasm documents a DOS real-mode program usable on early x86, but also specifies
DOS 5-compatible services. This is compatible with this goal's *tool scope*:
retain the FreeDOS services it actually needs and verify calls on the VA port.
Do not falsify DOS version results to avoid a missing implementation.

Inspect the pinned real-mode build recipe (for example OWDOS16.mak), license,
startup and libraries. Keep the project's accepted compiler if feasible; a
separate pinned assembler-build toolchain must not silently replace the kernel
compiler. Include the assembler's corresponding source, patches and required
notices in the public bundle. Source-build and trace its DOS dependencies; a
successful JWASMR help screen alone does not prove assembly works on VA.

Use the selected version's supported raw-binary and MZ output modes (commonly
-bin and -mz), verify their real syntax, and document exact commands in BUILD.BAT.
The COM sample must have the correct origin/layout and an explicit .COM output
name; the EXE sample must exercise actual relocation/startup. Both use .8086
(or the pinned equivalent -0 selection), DOS output/termination, no IBM BIOS,
no external libraries and no external linker. An assembler that can generate
newer instructions is acceptable; shipped programs and examples use the
8086-class contract. Check the generated instructions and outputs independently.

From a fresh normal boot of a disposable writable copy of the released 2HD
image, with B: empty, copy the original sample into a work directory on A:,
edit/save it with EDLIN, assemble with the guest JWASMR, run the generated COM,
assemble/run the MZ sample, and return to the shell for another command. Verify real output,
exit status where supported, written bytes and subsequent MEMMAP /CHECK. Include
one syntax-error case and a missing-input case that return control correctly.
An old executable left after an assembly failure must never count as its output.

Measure assembler peak/useful memory and largest-block needs with a small
repeatable sample. Publish per-tool minimum RAM measured on native configurations;
do not claim arbitrary large source files fit. Low-memory failure must be bounded
and leave the shell/MCBs usable. If JWASMR cannot run on the declared basic-disk
configuration, investigate source/build/layout first and consult with evidence
before dropping it or silently raising the supported minimum.

Write an original brief assembler quickstart. Upstream documentation and example
licenses can differ from code licenses; inspect them before bundling their text.
Links and original instructions suffice; do not copy an entire manual by default.

### 6.4. Exactly one bootable 2HD distribution disk

The user requires exactly one 2HD floppy for the practical distribution. This
supersedes the earlier permission for an additional tools disk. Put the native
boot components, kernel, fully packaged FreeCOM, all required tools including
MEMMAP/JWASMR, original samples, quickstart and necessary on-disk notices on
that same disk. The public normal-image output is one D88 containing one disk;
concatenated D88 disks, hidden second images, a required tools disk, host shares,
a hard disk or network downloads are not acceptable substitutes.

Select the already qualified PC-88VA native 2HD boot profile and record its
profile ID, cylinders, heads, sectors/track, bytes/sector, usable capacity,
BPB/FAT12 layout and D88 encoding. Do not infer geometry from the word 2HD,
assume a PC 1.44-MB profile or silently change it to the separate M16 2HC profile.
Confirm the selected profile against the actual accepted builder and boot
records. If qualification is missing, qualify it as part of this outcome.

Maintain a machine-readable capacity budget: boot/reserved/FAT/root-directory
space, each file's actual cluster allocation, directory use and remaining free
clusters. Reserve enough writable space for the demonstrated EDLIN/JWASMR sample
workflow, including editor temporary files and both generated programs. Measure
and record that working-space floor; fail the build if it is violated. Do not
fill the disk so completely that the advertised one-disk workflow cannot run.
The D88 container's file size is not the filesystem's usable capacity.

Fit the required set first. Remove optional programs, duplicate files and
unneeded documentation before making scoped, verified size reductions to
required builds. Do not omit a required program, break runtime resources or
start a broad redesign to meet an assumed budget. If the required set still
cannot fit, provide measured sizes, attempted reductions and a concrete
consultation; do not silently create a second distribution disk or claim PASS.

Corresponding source, full build documentation and legally required companion
license material may accompany the image as host-side archives/files; they do
not become another DOS tools disk. Preserve all license obligations and place
required on-disk notices where needed. QA fixtures and disposable formatting,
SYS-transfer or A:/B: regression media remain separate test artifacts, never a
second required distribution image in the public normal-disk output.

Prove ordinary boot, shell/text/memory operations and the editor/assembler
workflow with only this image in FDD1/A: and FDD2/B: empty. Maintenance programs
must also reside on A:; validate FORMAT/SYS and other destructive operations
separately using disposable target media, never the running release master.
Run editing/assembly on a writable disposable copy of
the same released bytes, preserving the original release checksum. Also verify
boot and read-only commands from a write-protected copy; writes are not required
merely to boot. Keep the accepted A:/physical B: functionality and test its
regression separately with disposable data media. Reuse the public QA builder's
infrastructure while keeping payload, outputs and acceptance identities distinct.
No QA autorun, automatic formatting or large startup RAM disk belongs here.

## 7. `make m18-disk`: isolated, reproducible and public-input-only

Implement this exact target in the parent task worktree's normal host Makefile:

```sh
make m18-disk
```

It must build the single normal M18 2HD D88 and public release bundle after the
documented pinned host-tool setup. One command must orchestrate kernel, packaged
VA FreeCOM, MEMMAP, JWASMR, required utilities, native boot components and image assembly;
no manual source edits, private image copying or hidden staging step may remain.
If dependency fetching is needed, use existing explicit pinned-fetch conventions,
validate hashes, provide a cache/offline path, and fail clearly on missing inputs.
Do not install host packages with implicit sudo or download a moving latest tag.

Use `build/m18/` (or an explicit equivalent isolated root documented by the
repository) for task-owned staging, objects, generated files and package builds.
Final public artifacts should be exposed under `dist/m18/`. The exact artifact
filenames are a versioned build contract, not guessed here. Print their paths
and hashes at successful completion. A supported build-root override is useful
for comparing two independent builds, but the no-argument target must work.

The build must:

1. Resolve declared parent/component sources and verify every source input.
   Iteration may include identified dirty task changes; final release sources
   must correspond to the committed revisions and packaged patches/source.
2. Isolate all components, including ones whose makefiles normally write into
   the source directory. Use out-of-tree builds or controlled task-owned source
   staging without discarding uncommitted implementation fixes. A parent output
   directory alone is not isolation if child makefiles overwrite shared objects.
3. Leave normal builds, QA outputs, other worktrees, source pins and private
   controls untouched. Support incremental builds and a fresh empty-output build.
   Target-specific cleaning must only remove its validated generated output root.
4. Create blank native media using the accepted public/synthetic builder, then
   install public native boot components, kernel, shell, utilities and data.
   Do not modify a private D88 template or copy a proprietary boot sector.
5. Verify geometry, FAT/BPB consistency, files/resources, checksums, CPU/port
   selection and capacity using independent checks where already available.
   Media/file order, FAT timestamps, unused bytes and container headers must be
   deterministic under the recorded reproducibility policy.
6. Fail nonzero and with a precise missing/failed component when anything fails.
   Never accept old artifacts after a failed build or silently fall back to
   a Mac path, unrelated installed compiler, old QA disk or IBM-PC COMMAND.COM.
7. Rebuild the release from a second clean isolated output root with the same
   pinned inputs and compare the intended reproducible bytes. Explain and fix
   unapproved nondeterminism instead of updating goldens to match it.

Expose separate verification targets, following repository naming conventions,
such as `m18-check` for public structural/host tests and `m18-qa` for optional
private VA guest execution. Do not make ROM access necessary for `m18-disk`.
The public build must succeed where `.private-evidence/` and the private ROM/docs
tree are absent or not mounted. Public CI must exercise that condition, not just
set a flag while still reading private inputs. Cross-directory dependencies
outside the public source/toolchain/cache allowlist must be detected.

`make m18-disk` is an artifact-production target. It must not deploy a release,
push a branch, launch an unbounded emulator session or perform destructive media
operations as a hidden side effect. Guest acceptance is a separately recorded
step required for M18 PASS.

## 8. Public bundle, sources and privacy

The public release-ready bundle must include:

- Exactly one bootable native 2HD D88, with full SHA-256 and size, a measured
  capacity/free-space budget, English README and normal VA/VAEG boot instructions.
  Any auxiliary source/license archive is a host-side companion, not a tools disk.
- A package/component manifest with actual versions, upstream references,
  source revisions, build options, license identifiers/notices, CPU requirements,
  VA adaptations, disk placement and tested capabilities/limits.
- Build scripts, configuration, original native boot/media generation and
  MEMMAP source, all necessary patches and corresponding source packages for
  redistributed modified/copyleft components as their licenses require.
- License texts/attribution and a practical source/build index. A moving URL or
  checksum alone is not a substitute for required corresponding source. Preserve
  each component's license; keep the repository's GPL-2.0-or-later root policy.
- Public synthetic tests and concise public-safe qualification results, clearly
  separated from private ROM-based execution evidence.

Read the actual included package licenses and provenance. Do not assume every
FreeDOS component shares the kernel license, that a public download grants every
redistribution right, or that dropping ROM files from a previously private D88
makes the remaining bytes public. If an input's permitted distribution is
unclear, resolve it or replace it with an authorized buildable component; do not
label an unresolved bundle public-ready.

Normal public disk construction must depend only on approved public inputs.
Private ROM/manual/disassembly-derived concrete values, captured disk contents,
private screenshots/traces and local secrets must not enter source commits,
public CI logs, manifests or release files. Reuse the repository's accepted
public/private promotion policy for hardware constants and native boot code;
this goal does not grant blanket permission to publish all new private findings.
Generic memory-map program logic and synthetic tests can be public, while
private candidate memory dumps/observations remain private as required.

Preserve the distinction between an image built publicly and the private
emulator/ROM used to qualify it. Scan archive members and generated files for
unexpected inputs; check source dependency provenance as well as filenames.
Do not upload actual private captures merely to show that the public disk works.

## 9. Acceptance matrix

Reconcile these gates with the accepted M13-M17 baseline and current technical
contracts. The superseded broad M18 package requirements are not cumulative.

| Gate | Required evidence |
| --- | --- |
| M18-BASELINE | User-selected d81bba18 prefix resolves to one recorded full parent SHA in integrated main history; M18 descends from that exact baseline; actual M16/M17 prerequisites, component pins, native memory contract, toolchains and matched control identified |
| M18-MEMORY-MAP | Before/after physical/resident/MCB ownership accounting; all proposed reclaimed or unavailable RAM explained |
| M18-MEMORY-REPAIR | Demonstrated stale/wasteful reservations or allocator/lifetime defects resolved; any disproved suspicion documented without fabricated savings |
| M18-ALLOC-EXEC | Real allocation/free/resize, fragmentation/coalescing, low-memory errors, COM/MZ EXEC and stable child termination |
| M18-CAPACITY | Accepted native capacities/boundaries and required minimum preserved; per-tool RAM requirements measured |
| M18-MEMMAP | Packaged ordinary MEMMAP, bounded chain validation, correct observer footprint, English help/check/output redirection and independent result comparison |
| M18-PACKAGES | Fixed section-6 basic set qualified, source/license/CPU/VA manifest complete; optional tools have explicit dispositions, no full-distribution parity gate |
| M18-ASSEMBLER | Guest EDLIN edit/save -> JWASMR COM/MZ assembly -> real EXEC/return; generated bytes, error recovery, measured RAM and stable MCBs |
| M18-CPU-VA | Guest CPU/library/startup dependencies audited, no FPU requirement, machine-specific I/O follows VA contracts |
| M18-NORMAL-DISK | Exactly one native 2HD D88 contains all mandatory payload; fresh boot and ordinary/editor/assembler/memory workflow on A: with B: empty; separate disposable maintenance-test media; usable prompt without QA harness |
| M18-CAPACITY-BUDGET | Verified 2HD geometry/FAT12 and cluster/file budget, measured sample-workspace reserve, no required second distribution disk; build fails on capacity violation |
| M18-ISOLATION | Exact `make m18-disk` succeeds from the documented clean setup, isolates child outputs and preserves QA/other worktrees |
| M18-REPRODUCIBLE | Two clean builds agree under the accepted byte-comparison policy; disk/package/source hashes and dependencies agree |
| M18-PUBLIC | Build without private trees/ROM, complete provenance/licenses/corresponding sources, no private payload in public artifacts |
| M18-REGRESSION | Relevant M13-M17 behavior, VA/VA2 input, A:/B:/media and writable filesystem paths remain qualified after layout changes |
| M18-CLOSURE | Current routing M13-M32, final records, child/parent topic commits, applicable CI and exact artifact handoff agree |

Test actual program behavior, not only `/?` output or a printed marker. Include:

- Fresh ordinary boot with no private interposer, debugger patch, guest-memory
  injection or fabricated DOS/BIOS result; trace-off must work.
- MEMMAP, real shell file/directory changes, MORE, redirection/batch, EDLIN
  save/reopen and the JWASMR workflow, followed by another successful command.
- FORMAT/SYS/CHKDSK on generated disposable fixtures using their documented
  supported profiles, including protection/error recovery. Independently inspect
  filesystem/file bytes and boot the SYS-produced result through the native path.
  Test optional copy/compare/filter tools only if included.
- Real media exchange and A:/B: work under the published memory configurations,
  preserving the M16 input/repeat/cursor/function-key behavior.
- A second fresh boot of the final public bytes and exact matched VAEG revision.
  Automated frontend input is allowed but must be labelled automated; do not
  claim physical-keyboard or hardware validation unless it actually occurred.

If VAEG needs a proven scoped fix, use an isolated topic and meaningful synthetic
tests, then repeat affected guest qualification with the new executable identity.
Do not alter the emulator to manufacture extra guest RAM or a successful utility
result. No blanket emulator redesign is authorized by this task.

## 10. Records, commits and exact handoff

Use existing canonical locations where possible. Required records include the
memory ownership/repair report, selected-payload manifest, build/reproduction
guide, MEMMAP specification, public/private acceptance summaries and current
milestone status/handoff. Preserve historical accepted bytes/results; add the
new qualification without overwriting an unexplained mismatch into PASS.

After local acceptance and scoped diff/privacy review, commit/push changed child
topics first, update parent gitlinks/locks and commit/push the parent topic.
Run applicable public/synthetic CI against the actual final behavioral revision.
Fix real failures and continue. Do not merge to shared main or force-push.
Avoid self-referential report hashes; put final tip/CI identifiers in a separate
durable handoff if required by the repository's reporting convention.

Deliver public files under the task's `dist/m18/` and retain concise private
evidence under the main repository's `.private-evidence/m18-memory/handoff/`.
Use unique candidate names for tested controls, not repeated overwrites. The
released candidate bytes must be exactly the bytes qualified; copying must
preserve size/hash. A later rebuild is a new candidate until equivalence is
established. Include corresponding source/license material alongside disk files.

The final response must state:

1. Confirmed causes and resolved ownership/layout issues; remaining justified
   reservations; before/after total free and largest block at matched stages.
2. Actual supported models, capacities, CPU level, mandatory/optional utilities,
   assembler source/build identity, measured RAM requirements and exclusions.
3. Exact `make m18-disk` build invocation and normal VAEG boot command.
4. Absolute path, size and full SHA-256 of the single normal 2HD D88 and the
   source/license bundle; geometry, used/free space and sample-workspace reserve;
   matched source/toolchain/VAEG identities and memory-map usage.
5. Private guest versus public CI results, normal versus QA image identity,
   commits/CI links and manual/hardware status.
6. Current numbering and a concrete M19 SASI-data handoff preserving M17's
   storage contracts and the newly qualified memory/distribution baseline.

## 11. Progress and consultation

Persist the current candidate, last good boundary, hypothesis, next discriminating
action, accepted repairs, package progress and remaining gates after meaningful
work. Every 30 minutes of active work save/present a concise checkpoint and
continue. Distinguish new evidence from pending builds/CI. Routine progress
updates may be more frequent; this is not an automatic background timer.

Prepare private `M18-consult-current.md` after 60 minutes without new useful
evidence/validated repair, two evidence-supported repairs leaving the same
failure unexplained, unresolved contradictions, or a required broad redesign or
mandatory-package/supported-capacity scope change. Include the precise question,
last correct/first wrong boundary, source/runtime evidence, attempts, alternatives,
recommended action, reproducible candidate identities and independent work.

Notify the user and continue useful independent work. Do not stack speculative
memory changes on a disputed path. A supported repair within the accepted design
can proceed when new evidence resolves the question; record that resolution.
Do not claim another reviewer was consulted unless it happened, or send private
material to another service without authorization.

Finish with `M18 PASS` only after all required memory, single-2HD basic disk,
MEMMAP, guest JWASMR workflow, isolated build, public bundle, guest/CI and handoff
gates pass. Full upstream-distribution parity is not an additional gate. Do not
end with routine PARTIAL merely because one experiment, build or package fails.
If an indispensable external input/access or a hard execution limit prevents
completion, finish useful independent work and leave the precise blocked resume
state. If every remaining action depends on a concrete unresolved design/scope
decision, use `M18 DECISION NEEDED` with the question and recommendation.
An ordinary technical defect is not an external access failure. Keep M19 onward
pending at M18 closure.

## 12. References and invocation

Checked while preparing this revision; pin and inspect the exact sources during
implementation. These references establish upstream capabilities, not VA PASS.

- [JWasm real-mode DOS program and requirements](https://github.com/JWasm/JWasm)
- [JWasm source and DOS16 build recipe](https://github.com/Baron-von-Riedesel/JWasm)
- [JWasm manual: CPU selection, BIN/MZ output and real-mode limits](https://baron-von-riedesel.github.io/JWasm/Html/Manual.html)

Invocation from the selected M18 task worktree:

```text
/goal Read docs/tasks/M18-memory-layout-basic-disk-goal-Codex.md and docs/freedos-pc88va-milestones-M13-M32.md in full. On ryzen, resolve the user-selected integrated main commit prefix d81bba18 to its unique full parent SHA, verify it is in the intended main history, and start or resume an isolated M18 topic worktree from that exact baseline and its component pins. Preserve existing work; do not substitute an advanced main tip or old M16/M17 branch. Complete the revised compact M18: account for conventional-memory/MCB ownership, repair proven waste/lifetime/fragmentation defects, provide MEMMAP, and build exactly one public-ready bootable native 2HD disk with the 8086-class selected MS-DOS 2.11-era tools and real-mode JWASMR. Preserve the common FreeDOS kernel and NECPC88VA FreeCOM and their DOS API level. Verify guest edit/assemble/COM-and-MZ-execute behavior on a writable copy on A: with B: empty; all mandatory tools must fit on that one disk. Keep companion sources/licenses outside the image and prohibit a supplemental tools disk. Preserve separate disposable QA media. Then implement isolated public-input-only make m18-disk, and deliver the exact tested single D88, sources/licenses, capacity budget and manifests, topic commits/pushes and applicable CI. Replace the earlier broad English-distribution goal; do not require full FreeDOS package parity or Japanese support. Keep current M13-M32 numbering, applying the older M18-M31 to M19-M32 mapping only if not yet adopted. Report every 30 minutes and use the consultation rules while continuing independent work. Preserve private/public separation and all earlier accepted behavior. Do not stop at a diagnostic result, weaken the mandatory gates or start M19.
```
