# M18 build, DOS payloads, and media tooling

M18 owns its complete parent-side build orchestration, helper modules,
producers, inspectors, settings, tests and fixtures under `tools/m18/`,
`config/m18/` and `tests/m18/`. `make m18-disk` exports the exact committed
M18 input paths and the exact pinned component gitlinks, checks them in an
allowlist-only Linux/amd64 container with networking disabled, builds every
program from source, composes and independently reads back a new native 2HD
D88, then repeats the whole build in a second clean container. No candidate
D88, generated DOS executable, ROM, private firmware, private disk, guest trace,
or prior milestone tool/config/test directory is a build input.

## Build interface

- `make m18-toolchain` prepares or verifies the pinned Linux/amd64 Open Watcom
  1.9 container. The official tool archive, Ubuntu base, apt snapshot, compiler
  identities and host test wheel are pinned.
- `make m18-disk` performs both complete source builds, compares D88 bytes and
  release records, validates payload hashes/FAT chains and root-directory
  capacity, and writes `dist/m18/` without overwriting an unrelated existing
  distribution. A repeat with the same inputs is allowed only if every public
  distribution file is identical. Use `M18_DIST=dist/m18-candidate-<id>` for a
  changed source identity.
- `make m18-clean` removes only the marker-validated Git-excluded `build/m18/`
  intermediate root. It preserves `dist/m18/`, the identity-pinned toolchain,
  and the host wheel cache.
- `make m18-host-tests` downloads/verifies the pinned Unicorn 2.1.4 wheel in
  the Git-excluded cache and runs the M18-local suite on Linux/x86_64. On other
  host architectures, `make m18-disk` runs all tests inside its pinned
  Linux/amd64 build container.

The topic branch must be committed and clean before `make m18-disk`. The build
checks the exact baseline ancestry, component gitlinks, source-archive hashes,
and fork/upstream URL identities. If a component checkout lacks its public
`upstream` remote, the script adds the exact URL from the committed lock to that
checkout's local Git configuration; it never changes component source or pushes
to a remote. Parent build inputs are exported from Git, not the mutable working
tree.

## Reproducible kernel banner date

Open Watcom 1.9 does not apply `SOURCE_DATE_EPOCH` to `__DATE__`. M18 uses
`kernel_cc.py` to pass the pinned component's existing `KERNEL_BUILD_DATE`
interface, derived in UTC from `config/m18/host-tooling.json`. The fixed-width
English month/day/year is build metadata, not the actual wall-clock build date.
The compiler path and every existing platform/INIT flag (including `-zu`) are
preserved. `finish_image.py` requires exactly one matching date in the linked
kernel and records the policy in the package manifest. No linked bytes are
patched and no component source is copied or modified. Earlier same-day
comparisons did not detect this banner-date defect; their old disk identities
remain history, not the new reproducible candidate.

## Separate allocator QA media

`make m18-allocator-qa` first performs the complete normal source build, then
composes a separate `build/m18-allocator-qa/media.d88` from its fresh, hash-checked
boot/shell/MEMMAP outputs and the original 8086 `tools/m18/qa/alloc.asm` probe.
The normal distribution is unchanged; QA payloads never enter its AUTOEXEC path.
Use a new `M18_QA_OUTPUT` for each candidate, and `M18_DIST` when the source
identity changes. The producer rejects existing QA output roots, stale source
pins, changed archives and payload drift. It builds the probe in the exact
compiler container from the full build and checks stage-1 byte equivalence.
No ROM, old D88 template or historical milestone helper is needed.

Boot a disposable QA copy and run `MEMMAP > BEFORE.TXT`, `ALLOC > RESULT.TXT`,
then `MEMMAP > AFTER.TXT` and `MEMMAP /CHECK`. ALLOC shrinks only itself while
retaining its own 512-byte stack, restores the DOS allocation strategy, and
performs 16 allocation/shrink/grow/free/coalescing rounds. It checks live-owner
preservation, failure across an occupied neighbor, zero-sized allocations,
invalid handles within its own payload (never corrupting a live MCB), exact
largest-block allocation, boundary word access and stable recovered capacity.
It returns zero only after all assertions, otherwise stage-specific failure and
exit code 1. DOS process termination releases outstanding child-owned blocks.
The reported baseline is actual AH=48h output in hexadecimal paragraphs.
Host tests prove an initial resize failure cannot be reported as success; they
do not substitute for running the complete probe under the real DOS kernel.

The same QA disk includes `QAEXEC.COM`, `CHILD.COM` and `CHILD.EXE`. From its
root directory run `QAEXEC > EXEC.TXT`, then `MEMMAP /CHECK`. The parent retains
its stack, reserves free holes through DOS and gradually releases a controlled
tail. Both formats must fail with DOS error 8 at exhaustion, then really execute
with exit 42 at their first sufficient budget. With an explicitly empty child
environment, the pinned FreeDOS contract predicts 6 environment paragraphs,
1 splitting MCB, and 24 COM process paragraphs: 31 tail paragraphs in total.
The COM fixture owns trailing startup-stack space: the loader writes a 24-byte
register frame before entry. Host tests reproduce that write and reject the old
16-byte fixture because its entry code overlaps the frame.
For the fixture MZ, the pinned loader counts the entire last 512-byte page:
6 + 1 + 16 PSP + (32 - 4 header) + 32 minalloc = 83 paragraphs. This existing
FreeDOS behavior is preserved rather than replaced by an MS-DOS or compact-image
formula. The fixture tests an actual MZ segment relocation and a bounded stack.
After reaching the boundary, 32 COM/MZ pairs must preserve guard owners/data and
recover identical capacity after each child, then restore the original largest
block and allocation strategy. These are fixture-specific thresholds, not
minimum RAM claims for other applications. Host child tests deliberately omit
the relocation and require a failing exit. Only real DOS guest execution can
qualify the parent's complete allocation/EXEC assertions.

## DOS executable entry lower bounds (not runtime peaks)

The build's `package-manifest.json` includes
`dos_executable_entry_lower_bounds` for every required external DOS utility,
read independently from the **composed** normal disk by
`tools/m18/qa/tool_ram_budget.py`. This accounts for the pinned FreeDOS
`DosExeLoader()`'s entire final 512-byte MZ page, plus the PSP and MZ minimum
extra paragraphs, with the MCB header reported separately. The literal linked
image length alone can **understate** this entry allocation. A Watcom
`maxalloc=FFFFh` may reserve a larger block up to the available DOS arena, and
runtime heap/stack/input/output demands, a child environment and concurrent
kernel/shell owners can impose further requirements. These per-file public
source-bound floors **do not measure useful runtime peaks or installed-RAM
minima**. Guest success/failure must be checked separately on the exact disk.

## Separate mixed-floppy data regression (not the normal disk)

`python3 -B tools/m18/qa/mixed_floppy_360.py --output /absolute/private-test-root/b-360.d88`
creates one **nonbooting, disposable** 40-cylinder/2-head/9-sector, 512-byte
sector, 360-KiB **2D-D88** FAT12 B: test disk. Raw 360-KiB `.img` is not
recognized by the matched emulator and must not be substituted. The M18-local recipe and
negative host tests are in `config/m18/mixed-floppy-360.json` and
`tests/m18/test_mixed_floppy_360.py`; neither imports an older milestone's
runtime inputs. Use a disposable copy of the *same tested normal* 2HD disk as
A:, then write and read a file on B: with ordinary DOS COPY/TYPE; stop VAEG
before `--inspect` readback or examining the final D88/FAT chains. This does
not add a second distribution disk or imply that the **2HD-only** M18 FORMAT,
CHKDSK and SYS programs support a 360-KiB profile. Do not feed this QA image
to normal `make m18-disk` or change another milestone's accepted fixture.

## Optional private interval readback

`tools/m18/qa/interval_readback.py` is a separately invoked M18-local inspector;
it never runs during normal media construction. Pass `--manifest` the public
`build-manifest.json`, `--normal` its exact normal D88, `--carrier` the
same build's `carrier.json`, `--snapshot` an actual guest `MEMMAP > FILE.TXT`
readback, `--installed-kib` the **installed** 256/384/512/640-KiB capacity,
and `--output` a new path **outside** this checkout. It independently checks
source disk/carrier identity, linked resident/first-MCB adjacency, every MCB
header/end/owner PSP, memory-top bounds, paragraph totals, observer footprint,
and the temporary carrier/INIT/scratch/ring placement and lifetimes. It does
not infer hardware/BIOS ownership from DOS MCBs or measure an in-program peak.
Do not publish its guest snapshot or generated numeric interval report; the
synthetic host tests cover corrupt headers, ownership, missing rows, totals,
RAM-top drift and placement errors without private inputs.

## JWASMR without a numeric coprocessor

The pinned JWasm source converts REAL4/REAL8 decimal initializers through Watcom `strtod()`. A DOS16 `-0` compiler flag alone is not proof that a floating-point coprocessor is unnecessary. The clean JWASMR link therefore verifies that both the pinned Watcom conversion object and its DOS **software 8087 emulator** are present; `noemu87.lib` is rejected. Matched VA and VA2 guests with the optional coprocessor explicitly disabled assembled and executed a small 8086 COM file containing a real-number initializer on the same normal disk; its output bytes and subsequent MCB state were inspected privately. The assembler can emit later CPU/FPU instructions at a user's explicit request; this is not a promise that such *generated* programs run on an 8086/V30 without a coprocessor. The shipped samples use only their original 8086 DOS contract.

## Separate guest-workspace readback

`python3 -B tools/m18/qa/workspace_readback.py --normal dist/m18/PC88VA-M18-2HD.D88 --manifest dist/m18/build-manifest.json --copy COPY.d88 --edit EDIT.d88 --build BUILD.d88 --output /absolute/private-evidence/workspace.json` is an explicitly invoked QA inspector, **not** an input to `make m18-disk`. Use separate disposable copies of the exact release candidate, stop after each successive source-copy, EDLIN save and BUILD.BAT command, and keep the unmodified normal disk as the baseline. The inspector binds it to the build manifest, checks D88/FAT readback and an unchanged boot sector and release root, checks editor backup/source copies and both executable outputs (including a real MZ relocation), and fails if any settled checkpoint exceeds the committed cluster reserve. Keep the JSON output and guest media in Git-excluded private evidence; do not put private disk contents, hashes or observations in the public source tree. A snapshot taken during a write may have inconsistent FAT state: only settled completed guest runs qualify. Settled checkpoints alone do **not** measure instantaneous in-process peak. The owner removed the instantaneous disk-workspace-peak requirement from M18 acceptance; keep the 32-cluster reserve, stage readback, source-lifetime review and ordinary disk workflow without claiming an unmeasured peak. For the shipped successful sample, EDLIN renames the original to a backup before writing the new source, and JWASMR opens the one selected `-bin`/`-mz` output for writing without a listing or error file; no separate temporary payload is configured. The policy budget retains additional headroom for errors, filesystem metadata and future changes. Rerun guest checks if those source paths or build options change.

## Separate disposable B: preparation

`python3 -B tools/m18/qa/blank_data_media.py --output /absolute/private-test-root/b-target.d88` creates a **nonbooting**, empty, public-profile native 2HD FAT12 B: target with a distinct QA label, using only `config/m18/media.json` and the M18-maintained FAT/D88 builder. It verifies its own sector geometry, two FAT copies and empty directory through independent readback, rejects existing files and refuses output inside the public source tree. Run it separately for each B: disk, preserving both before/after bytes and the exact normal A: disk used for testing. It neither reads nor replaces the distribution and is never required by `make m18-disk`.

## Milestone-local layout

- `build_image.py`, `build_image.sh`, and `finish_image.py` own the complete
  clean build and output records.
- `build_loader.py`, `loader_profile.py`, `build_compressed_kernel.py`,
  `verify_m13_linked_placement.py`, `media.py`, and `compose_image.py` are
  maintained M18-local copies of the required algorithms at M18 start. Their
  M17 and M13 source lineage is documented in the files. Only M18 tests and
  configuration are used here; no earlier parent milestone is imported.
- `edlin/`, `assembler/`, `memmap/`, `programs/`, and `maintenance/` contain
  source builders for EDLIN, real-mode JWASMR, MEMMAP, MORE, and the three
  profile-bounded maintenance applications. All application code targets
  8086 real mode; the native VA loader/kernel remains platform-specific.
- `manifests/m18-components.lock.json` pins the exact public kernel, FreeCOM,
  COUNTRY.SYS, EDLIN and JWasm gitlinks and source-archive hashes. The shared
  `manifests/toolchains.lock.json` supplies identity-pinned compiler and
  toolchain dependencies.
- `verify_isolation.py` rejects any earlier milestone directories, path
  references, symlinks or transitive code dependencies from the allowlisted
  export. `verify_source_audit.py` rejects private/generated-media inputs and
  checks the public source/package lock.

The fixed 2HD output is 80 cylinders × 2 heads × 8 sectors/track × 1024 bytes,
FAT12, 1280 sectors, 192 root entries, one-sector clusters and a single boot
volume label. The media composer allocates the stage-2 loader contiguously for
the native boot code, writes all file bytes from the fresh source-build
payloads, emits fixed FAT timestamps, and verifies exact D88/FAT readback.
`capacity-budget.json` is a host allocation record and policy floor, not a guest
measurement of the complete edit/assemble workflow.

## Tool scope and limits

The disk has the native boot loader/kernel, FreeCOM, COUNTRY.SYS, EDLIN, MORE,
MEMMAP, JWASMR, CHKDSK, FORMAT and SYS, plus English/ASCII starter sources and
license notices. `packages.json` records version, source, license, CPU, build
options, VA-specific adaptation and gate status; generated `package-manifest`
records add exact hashes and DOS MZ allocation data.

MEMMAP discovers the MCB list through the pinned FreeDOS interface, validates
DOS version/layout and PSP ownership, and reports managed DOS MCB accounting.
Its MZ `maximum allocation` equals `minimum allocation`. The build record
separates the linked-image lower bound from the pinned FreeDOS whole-page initial
allocation; neither is the runtime footprint. Watcom startup can grow heaps.
After priming stdout, MEMMAP calls the documented OW 1.9 `_nheapshrink` and
`_fheapshrink` APIs to return only its unused heap tails, preserving live data,
stack and buffering. It fails closed if either call fails, then measures actual
MCB ownership including its environment. It never resizes to a guessed linked
minimum or frees another owner. Physical/reserved memory is labelled unavailable. CHKDSK is read-only.
FORMAT writes filesystem metadata only to a B: volume with a readable, valid
native 2HD BPB from prior preparation. SYS
installs validated native boot files to prepared B: media and writes the boot
sector last. None of the
maintenance commands supports other floppy profiles, SASI/SCSI, hard-disk
boot, or FAT16.

Host success does not establish DOS runtime behavior, free-memory ownership,
VAEG compatibility, guest RAM minima, disk-space peak use, or hardware support.
The required shell, editor, pager, memory map, assembler, sample workflow and
maintenance operations must be qualified against the exact output D88 before
M18 completion. Every report must name guest/emulator/hardware gates that were
not run; a clean link or synthetic CPU test is not a substitute.
