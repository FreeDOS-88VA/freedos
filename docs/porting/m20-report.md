# M20 report: restart on the FreeDOS 1.4 release baseline

Status: **IN PROGRESS — kernel and FreeCOM restarted on the FreeDOS 1.4
release sources and booting on VAEG.** No M20 distribution is designated.
Hardware is **NOT RUN**.

## Decision

The owner chose to restart the PC-88VA port on the FreeDOS 1.4 release
components (option A), so that the baseline is identical to the FreeDOS 1.4
PC comparison control:

| Component | Repository | Tag | Commit |
| --- | --- | --- | --- |
| Kernel | `https://github.com/FDOS/kernel` | `ke2043` | `4f7bdda16a84c416a82a2616aa67335ca4f2bd74` |
| Shell | `https://github.com/FDOS/freecom` | `com086` | `f1b8f4f464eae5a70348b6d362484d733d45c427` |

Correspondence with the FreeDOS 1.4 release was checked against the public
FreeDOS 1.4 Floppy Edition archive (SHA-256
`45b1fa7c52dd996c3bfa5e352ffcd410781b952a6ad629f15a4c9ec4bbaefc5a`), boot
image `144m/x86BOOT.img`:

- `KERNEL.SYS` (UPX-compressed) is dated 2021-05-14, matching `ke2043`
  (2021-05-13); earlier PC runs of this image reported kernel 2043.
- `FREEDOS\BIN\COMMAND.COM` identifies itself as FreeCOM `0.86 - WATCOMC -
  XMS_Swap`, built `Dec 30 2024 22:10:51`, matching `com086` (2024-12-30).

This establishes the release identity of the baseline, not byte identity of
a local rebuild; reproducing the release binaries is not an M20 requirement.

Rules: `AGENTS.md` now names the official FDOS repositories as `upstream`
from M20 onward and keeps `lpproj` as a reference remote for NEC PC-98/DBCS
patches, imported selectively with recorded provenance and classification.
The MS-DOS 4 COMMAND.COM work is outside the initial M20 scope and will be
integrated separately.

`tools/configure_component_remotes.sh` and the milestone-neutral
`tools/verify_scaffold.py` now configure and require the M20 roles
(`upstream` = FDOS, `lpproj` = lpproj); `make verify-scaffold` passes with
them. Historical M10/M14/M17 tooling still encodes `upstream` = lpproj and is
left unchanged as history; it fails only when run against the M20 remote
layout, and old commits keep their own rules.

## Starting point

- Parent branch `m20/freedos-1.4-base`, created from M19 mainline
  `ba868e2e33447fe5fcb3a2bed0711464f7968d82`
  (`fix/m19-shell-startup`), plus the docs-only banked-memory research note.
- Component pins are still the M19 pins; the M20 component branches have not
  been created yet.
- The released M19 MS-DOS 4 COMMAND preview, stable M18 distribution and the
  M19 branches (including `experiment/m19-kswap-va`) remain unchanged and
  serve as regression controls.

## Survey of the M19 components against the baseline

Kernel (M19 pin `2dba27f199b5748553143cec0568da8596210088`):

- Its merge base with FDOS is exactly `ke2043`; no FDOS commit after `ke2043`
  is included. FDOS has since released `ke2044`–`ke2046` (318 commits).
- On top of `ke2043` it carries 341 commits from `lpproj` NEC PC-98 work
  (through `c9ce245`, 2026-06-15) and 136 project PC-88VA commits.
- The 136 PC-88VA commits change 143 files (+18,848/−136 lines); outside
  `pc88va/` they still touch 46 shared files (+3,659/−136 lines), such as
  `kernel/asmsupt.asm`, `config.c`, `main.c`, `intr.asm`, `dsk.c`, `task.c`,
  `entry.asm`, `kernel.asm`, `int2f.asm`, `memmgr.c` and `fatfs.c`. Part of
  this work is expected to depend on the PC-98 infrastructure underneath it.

FreeCOM (M19 normal pin `62dfacb4a88ca0a2b5a2b9b9c2c8ad5f8c917699`):

- Based on FDOS commit `e24bd7e` (2025-02-21), 36 commits after `com086`;
  FDOS master is 11 commits further ahead.
- 55 commits (`lpproj` DBCS and project PC-88VA work) are not in FDOS.
- Restarting on `com086` therefore also drops the 36 upstream commits after
  0.86; each one that M19 relied on must be reviewed and, if needed,
  imported explicitly.

The repaired kernel-swap work (`fix/kswap-state`) is common FreeCOM code
qualified only on PC; it is a candidate for separate import, not baseline.

## Plan

1. Inventory (first pass done, see `docs/porting/m20-inventory.md`):
   classify each M19 PC-88VA kernel/FreeCOM commit and each relevant
   `lpproj` commit as PC-88VA required, shared platform
   infrastructure needed by PC-88VA, PC-98 specific, or common fix. Record
   dependencies and the M19 defects already found in each area. No source
   change in this step.
2. Create component branches from `ke2043` and `com086` in the
   `nakatamaho` forks; keep a non-PC-88VA build of each that behaves as the
   baseline.
3. Port the PC-88VA adapter first with the smallest required shared
   infrastructure; import PC-98 changes one at a time only for a stated
   PC-88VA need.
4. Establish M20-local build/media tooling under `tools/m20/`, `config/m20/`
   and `tests/m20/`, with a clean public two-build gate before the first
   published M20 build checkpoint.
5. Qualify on PC (baseline behavior of the non-VA build) and VAEG
   (startup, file I/O, COM/MZ, RAM matrix including stale retained
   settings), bisecting any regression to the baseline, an imported PC-98
   change or the VA adapter.
6. Publish `docs/porting/m20-memory-layout.md` before the M20 layout differs
   from the M17 contract.

## Kernel on the FreeDOS 1.4 baseline

Component branch `m20/pc88va` in `nakatamaho/fdkernel`, from `ke2043`:

1. `b479209` — backport of lpproj `d1e1ead` (BIG_SECTOR, classified shared
   infrastructure needed by PC-88VA); the original `config_init_buffers()`
   is kept verbatim for 512-byte builds.
2. `551c8da` — the M19 `pc88va/` adapter tree, unchanged.
3. `4cc954c1a759b036a554acb79e777825ba3a8c61` — the M19 shared-file
   integration, ported without the underlying lpproj changes.

Findings:

- **The M19 kernel never had a working non-VA build.** Built for the IBM PC
  target, its shared-file changes altered calling conventions and common
  code, and that kernel hung after the banner (QEMU, FreeDOS 1.4 floppy).
  All such changes are now confined to PC88VA builds; the guards were
  generated with `tools/m20/confine_platform_changes.py` and reviewed, with
  `fatfs.c` `rqblockio()` rewritten by hand for readability.
- **Gate:** `tools/m20/pc_baseline.py` builds `ke2043` and the M20 commit for
  the IBM PC target (8086, FAT32, Open Watcom 1.9, no UPX) and compares
  `KERNEL.SYS`, `SYS.COM` and `COUNTRY.SYS`: **identical**. The unmodified
  baseline kernel also boots the FreeDOS 1.4 floppy under QEMU with its
  FreeCOM 0.86 (scratch smoke test; PC control only).
- Part of the M19 VA code depended on lpproj `f342d33` (an adaptation of
  post-1.4 FDOS `3d1ba0d`, master environment built during FDCONFIG
  processing, and `FSTRCPY` in INIT). It is not imported; the VA code uses the
  `ke2043` model (`CONFIG=` menu export via the near `envp`).
- Kept only for PC88VA builds, as qualified in M19: `blk_driver()` clears the
  transfer count on an invalid unit and rejects `r_command == NENTRY`
  (`>` → `>=`). The latter addresses an upstream out-of-range dispatch;
  recorded as an upstream defect candidate, unchanged for other builds.
- lpproj `GUARD_MEMORY_ON_INIT` (`e83ebfa`), NEC98/DBCS variants and other
  lpproj shared changes are not taken (see `docs/porting/m20-inventory.md`).

M20 tooling: `tools/m20`, `config/m20`, `tests/m20` are maintained copies of
the M19 normal-distribution build (MS-DOS 4 QA omitted); isolation forbids
M00–M19 inputs; `manifests/m20-components.lock.json` pins the kernel above and
FreeCOM's M19 normal pin as an explicit interim. `tools/qa/current_components.py`
selects the M20 lock and requires the kernel/FreeCOM pins to descend from
`ke2043`/`com086`.

**HOST (local):** `make m20-host-tests` passed; `make m20-disk` built two
identical disks from clean exports (D88 SHA-256
`906504f733e3f8ca3a722708169415013518e30b13c89d7faa73dc64cf9e22b9`), with
linked-placement verification, source/privacy audit and the acceptance
instance inside the build.

**Published work checkpoint:** kernel branch `nakatamaho/fdkernel`
`m20/pc88va` = `4cc954c1a759b036a554acb79e777825ba3a8c61` (pushed before the
parent); parent `m20/freedos-1.4-base` =
`4471245bc2a845efe9d0bab25a58768b8db128bb`, remote equal to local.

- Fresh public rebuild: a new clone of that revision with submodules ran
  `make m20-disk` and produced the same D88 SHA-256 `906504f7...`.
- Native CI `M20 isolated native 2HD source build`, run `37171083835`,
  attempt 1, head `4471245`: success (host suite, source audit, toolchain,
  PC baseline identity `identical: true`, two complete builds, allocator QA
  media, acceptance instance, clean checkouts). The runner produced the same
  D88 SHA-256.
- Scaffold validation on the same head: success.
- Historical workflows M01-M09 also triggered on the new branch name and
  failed. They are not M20 gates and are left unchanged: M03/M04/M04R1/M05
  predecessor-scope checks (also failing on other new branches, e.g.
  `experiment/m19-kswap-va`); M06/M07/M07R2-R6 M04R1 `COPYING` digest
  (identical blob; the upstream `ke2043` `.gitattributes` `* text eol=crlf`,
  which lpproj had disabled, gives CRLF in a fresh checkout); M01R1 expects
  lpproj's form of the kernel date-macro line; M02 tracked-path check on an
  M18 task document; M08/M09 drifted external Ubuntu package index.

**VAEG (local candidate above, private evidence retained):**

| Model | Installed | Retained selection | Workflow | Result |
| --- | --- | --- | --- | --- |
| VA2 | 640 KiB | none | startup, COM/MZ assembly and execution, file write/readback, MCB | pass |
| VA | 640 KiB | none | same | pass |
| VA2 | 512 KiB | 640 KiB (unchanged before/after) | startup, file write/readback, MCB (no assembler, known M19 limit) | pass |

The resident kernel and work area end 16 bytes lower than in M19 (largest
free block at 640 KiB: 359,472 bytes). A first 512 KiB run used `MORE` in an
injected script; `MORE` consumed the following keystrokes, so that run is a
retained test-script failure, not a guest result.

## FreeCOM on the FreeDOS 1.4 baseline

Component branch `m20/pc88va` in `nakatamaho/freecom_dbcs2`, from `com086`
(FreeCOM 0.86 as shipped in FreeDOS 1.4):

1. `876eaf8` — deterministic `FREECOM_BUILD_DATE`/`TIME` macros (project
   `855281a`; defaults unchanged; lpproj `middle_version()` context dropped).
2. `1d41828` — `build.sh pc88va` / `config.std` `-DPC88VA` selector, reduced
   from lpproj's platform selector to the PC-88VA target only.
3. `b16d851` — PC-88VA console hooks: cursor position/shape and `goxy()`
   through the VA text BIOS INT 83h; DOS AH=06h key check; fixed 80x25;
   no PC BIOS tick counter in `COPY`; `CLS` through INT 83h AH=02h
   `ESC[2J ESC[H`.
4. `18b692a2a8db6fb46dee1d64dbe0297d1d5ab530` — PC-88VA feature set
   (project `450d49b` + `62dfacb`).

Findings:

- Plain `com086` builds with the pinned Linux Open Watcom 1.9 toolchain and
  its own host tools; the post-0.86 upstream build changes are not needed.
  The M20 recipe no longer compiles the M19-era `utilsc/critstrs.c`;
  FreeCOM 0.86 `ptchsize` sets the 3 KiB heap.
- Keyboard input needs no VA change: FreeCOM 0.86 already reads through
  DOS AH=07h; only cursor, `CLS`, key status, screen size and the `COPY`
  tick counter used PC BIOS services.
- The M19 FreeCOM used lpproj's enhanced-input editor; M20 uses FreeCOM
  0.86's own line editor with the VA cursor hooks. lpproj DBCS/NEC98 code is
  not taken.
- **M19 FreeCOM `CLS` did not clear the VA screen**: its form feed is
  rejected by the VA kernel console and the lpproj generic branch did
  nothing else. M20 clears through the VA text BIOS, as the project's
  MS-DOS 4 COMMAND port does (VAEG screenshot checked).
- Not imported: project `6cd372b` (malformed date input returns a syntax
  error; an upstream FreeCOM behavior, recorded as an upstream defect
  candidate) and `9cf57b2` (`MEM` alias; `MEMORY` is disabled on the VA).
- **Gate:** `tools/m20/pc_baseline.py` now also builds `com086` and the M20
  FreeCOM in the default configuration (Open Watcom, XMS swap, English):
  `COMMAND.COM` is identical apart from the embedded build timestamp.

Local HOST: `make m20-host-tests` passed; `make m20-disk` built two
identical disks, D88 SHA-256
`e25abef6df563dc418e04f4f7a766c112574812d39c507147df115ac95a7877d`.

VAEG with this candidate (private evidence retained): VA2/640 and VA/640
full workflow pass; VA2 installed 512 KiB with retained 640 KiB (unchanged
before/after) reduced workflow passes; startup screen shows FreeCOM 0.86;
`CLS` clears the console. The largest free block at 640 KiB is 359,312
bytes, 160 bytes below the M19 FreeCOM.

**Published:** FreeCOM branch `m20/pc88va` = `18b692a` pushed before the
parent; parent `m20/freedos-1.4-base` = `2829bcb982dd1ee22e9f0f2e7af207dd024e6931`,
remote equal to local. A fresh public clone of that revision rebuilt the same
D88 (`e25abef6...`). Native CI run `37172655995`, attempt 1, exact head:
success, including kernel `identical: true` and FreeCOM
`freecom_identical_except_timestamps: true`, and the same D88 hash; scaffold
validation success. Historical M01-M09 workflows fail on this branch for the
reasons recorded above.

## Floppy set: utilities disk with FIND

Survey and selection: `docs/porting/m20-floppy-survey.md` (owner approved the
proposed English 3-disk set and porting Turbo-C-only packages to Open
Watcom; Open Watcom 1.9 remains the only compiler).

First program, establishing the pipeline:

- Components `find` (FDOS `a6e245d`, FreeDOS 1.4 FIND 3.0b), `kitten`
  (`6265435`, LGPL-2.1) and `tnyprntf` (`450ab90`, GPL-2.0), pinned as parent
  submodules. `git archive` omits find's nested submodules, so the libraries
  are pinned separately and staged as `find/kitten` and `find/tnyprntf`; a
  host test checks that the pins equal find's own submodule commits.
- `tools/m20/utilities/build_find.py`: Open Watcom 1.9, find's Watcom options
  plus explicit `-0` (8086), no UPX; `FIND.EXE` 13,430 bytes, built-in English
  messages.
- `config/m20/utility-disk.json`: non-bootable utilities disk for drive B:
  (`freedos-PC88VA-M20-UTIL.D88`, label `M20-UTIL`) with `FIND.EXE`,
  `README.TXT`, `COPYING` (GPL-2) and `KITTEN.LIC` (LGPL-2.1).
- The build composes and reads back the disk, compares it across the two
  clean builds, publishes it with `utility-manifest.json`, includes the new
  component archives in the source bundle, and `verify_distribution` /
  `verify_source_audit` check it. The component set is read from the lock
  (`tools/m20/component_set.py`).

Local HOST: host tests passed; `make m20-disk` built both disks twice with
identical bytes (system D88 unchanged at `e25abef6...`; utilities D88
`af74b6ae566630b750b3521c31450af8717a7504ff473a73251f962c72a8c107`);
`make m20-accept` passed.

VAEG (VA2/640 and VA/640, system disk in A:, utilities disk in B:): `FIND`
matching, `/C` count (8 `GNU` lines, equal to the host count), `/I`, and exit
codes 1/0 for no match/match pass; both disks are otherwise unchanged.

## Utilities disk: eight FreeDOS 1.4 programs

Added `sort`, `xcopy`, `label`, `move`, `append`, `nlsfunc` and `devload`
next to `find`, each pinned at its last upstream commit on or before the
FreeDOS 1.4 release (2025-04-09), plus kitten `3b9947f` referenced by sort,
label and move. `tools/m20/utilities/build_tools.py` reproduces each
program's own Open Watcom or NASM settings (explicit `-0`, no UPX); host
tests check the cutoff selection and each program's own kitten/tnyprntf
submodule commits. No program needed a source change for the VA.

Findings:

- MOVE overflows the Open Watcom default 2 KiB stack (PC and VA); it is
  built with `-k8192` (build setting only).
- FC built with Open Watcom does not return when comparing files, on PC
  (FreeDOS 1.4 kernel) as well as on the VA; FreeDOS 1.4 shipped a Borland
  build. FC is deferred to a fork-based investigation.
- CHOICE `/T` reads the PC BIOS tick counter at `0040:006C` (VA system
  common area), DELTREE prompts through INT 16h, and COMP uses NASM 0.98
  `equ word` syntax rejected by NASM 2.15; these need source changes in
  component forks and are deferred.
- A submodule-add mistake briefly left sort/xcopy/label/move/kitten at the
  current upstream HEAD; the new cutoff host test caught it before any
  published build.
- MEMMAP rejected NLSFUNC's DOS-owned package block (owner `000Ah`,
  `SC NLS P`, found in a VAEG guest memory dump). MEMMAP now treats owners
  below `0040h` as reserved system owners; owners at or above `0040h`
  without a PSP block are still rejected. This changes the system disk.

Local HOST: host tests passed; two identical builds: system D88
`35736d8ef4a7bbe6bf7b4c29d8612e4b7ddf80afea05d15032f5071aa373acb3`,
utilities D88 `c4d2446aab00d9c7b0149606269bb00b1754b11885b5f93cf1f949aa4f08aed2`;
`make m20-accept` passed.

VAEG (system disk A:, utilities disk B:): VA2/640 and VA/640 pass SORT
(line set and order), XCOPY into a subdirectory, MOVE rename, LABEL
(`M20TEST`), DEVLOAD help, NLSFUNC (exit 0), APPEND (opens `KITTEN.LIC` from
B:), and MCB validity after the TSRs. System-disk regressions with the new
MEMMAP: VA2/640 full workflow and VA2 512/640-retained reduced workflow pass.

## Utilities disk: CHOICE and DELTREE from project forks

The owner approved forks for programs that need source changes. Forks
`nakatamaho/choice` and `nakatamaho/deltree` start at their FreeDOS 1.4
cutoff commits (`fba7772`, `ed47278`) with one PC88VA-only commit each:

- `aa63ef2`: CHOICE times `/T` with DOS function 2Ch (centiseconds, midnight
  wrap) instead of the PC BIOS tick counter at `0040:006C`;
- `ca8e912`: DELTREE reads its confirmation key with DOS 0Bh/07h instead of
  INT 16h, keeping the typeahead rule.

The utilities builder passes `-DPC88VA` for them. `tools/m20/pc_baseline.py`
now also builds each forked utility without its PC88VA defines from the
upstream base and from the pinned fork commit: both are byte-identical. A host
test checks the fork bases against the cutoff rule.

Local HOST: host tests passed; two identical builds; utilities D88
`8ece7ea5168931912c865649b0dd3c67caf40b569406f42f2fb13d667831ee07` (system
D88 unchanged); `make m20-accept` passed.

VAEG VA2/640 and VA/640: CHOICE `/T:N,2` returns the default after the
timeout (errorlevel 2) and a typed `Y` returns errorlevel 1; DELTREE `y`
deletes a directory tree and `n` keeps it.

## Utilities disk: COMP and FC from project forks

- `nakatamaho/comp` `5269401` (base `ddb4e39`): NASM 0.98-only `equ word`
  syntax removed. Built with its documented command by NASM 2.15, `COMP.COM`
  is byte-identical to the FreeDOS 1.4 package binary (SHA-256 recorded in
  the lock as `release_binary`; `pc_baseline.py` checks it for forks whose
  upstream base cannot be built). `COMP.LIC` carries the MIT notice extracted
  from the source.
- `nakatamaho/fc` `543205a` (base `5591875`): FC's LFN calls test the carry
  flag as zero/non-zero (Open Watcom reports 0/FFFFh) and also treat a
  returned AX=7100h as failure.

FC finding: the upstream Open Watcom build of FC loops forever on a DOS
without LFN support. A probe program showed that **the FreeDOS 1.4 kernel
built without FAT32 answers INT 21h AH=71h with AL=0 and the carry flag
unchanged** (the `case 0x71` error return exists only under `WITHFAT32`).
The PC-88VA kernel is built without FAT32, and the upstream PC kernel built
with `XFAT=16` behaves identically, so this is the selected upstream
behavior, not a VA defect, and the kernel stays unchanged. Open Watcom's
`intdosx` clears the carry flag before the call, so FC took the unsupported
call as success. FreeDOS 1.4 shipped a Borland FC; with no byte baseline,
the lock records an explained `baseline_exemption`, and a host test keeps the
fork diff limited to the LFN-failure tests. FC passes on PC with FAT32 and
FAT16 FreeDOS 1.4 kernels.

Local HOST: host tests passed; two identical builds; utilities D88
`fe088486effc80d7201bc754c8e4c0c6d3721e4bbba68945de300f90c4f6feec` (system
D88 unchanged); `make m20-accept` passed.

VAEG VA2/640 and VA/640: FC text compare (no differences, exit 0;
different, exit 1), FC `/B` (exit 1), COMP equal ("Files compare OK") and
different files pass. Regressions of the other utilities and of
CHOICE/DELTREE pass on VA2/640.

## Utilities disk: ATTRIB and the remaining Turbo C programs

- `nakatamaho/attrib` `21f44cc` (base `f670ebb`): `__WATCOMC__` branches for
  the exact header name `TYPES.H` and a `stpcpy()` replacement; the
  Borland/Turbo C source is unchanged. FreeDOS 1.4 shipped a Borland build,
  so the lock records a baseline exemption with a `watcom-branches-only`
  host check (dropping the `__WATCOMC__` branches reproduces the upstream
  file). PC (FreeDOS 1.4 kernel) and VAEG VA2/640, VA/640: set, clear and
  list attributes, `/S` recursion, read-only file protected from `DEL`.
- Utilities D88 with ATTRIB:
  `7e3f8360e50043927265d2ee33ab45ac645ac62129ce75a67f532da76b13e7dd`
  (system D88 unchanged).

Owner decisions: pin `wpp` and port TREE; defer SHARE; create project
repositories for REPLACE, EXE2BIN, SWSUBST and UNDELETE.

- Shared toolchain lock: Open Watcom 1.9 `binl/wpp` (C++16 compiler) added
  and verified like the other host tools.
- `nakatamaho/tree` `29ba525` (base `f4e7e2e`, pdTree 1.03, public domain):
  `w32fDOS/watcom/w32fDOS.cpp` translates the Borland asm DOS layer to
  `intdosx` (AX=7100h after an LFN call counts as the carry Borland sets);
  `__WATCOMC__` branches for the header name and `_getdrive()`; PC88VA builds
  default to the ASCII tree (the VA character set has JIS X 0201 katakana
  where code page 437 has box-drawing characters) and a fixed 80x25 console
  instead of the PC BIOS data area. The Open Watcom build needs `-k32768`
  (Borland small-model stacks use the rest of DGROUP; the 2 KiB default
  overflows). The baseline check is now `platform-branches-only`: dropping
  `__WATCOMC__`/PC88VA branches reproduces the upstream files and new files
  may only be Open Watcom-only (also used for ATTRIB).
- PC FAT32 and FAT16 FreeDOS 1.4 kernels and VAEG VA2/640, VA/640: TREE with
  `/F`, default ASCII lines, volume label and serial number, whole disk.
- Utilities D88 `28e09950df58883a66c1b231e1e75d2f76827d5b5372ef9a4deca6f2854da74a`
  (system D88 unchanged).
- SHARE: deferred (TSR, Turbo C/gcc-ia16 only, kernel SHARE hooks; little
  use on a single-floppy system).

## Utilities disk: REPLACE and EXE2BIN from project package imports

Owner-approved new repositories `nakatamaho/replace`, `nakatamaho/exe2bin`,
`nakatamaho/swsubst` and `nakatamaho/undelete` start with verbatim imports
of the FreeDOS 1.4 repository package sources (`SOURCE/`, `DOC/`, English
LSM; binaries and translations not imported) and a `PROVENANCE.md` with the
package URL, zip SHA-256 and member hashes. The EXE2BIN package metadata was
updated after the release, but its source files date from 2006.

- REPLACE `bcc2e23`: an `#elif __WATCOMC__` branch maps the Borland
  `<dir.h>`/`<dos.h>` functions (find, disk free, file time, `_chmod`);
  built with `-k8192` (stack, as for MOVE/TREE).
- EXE2BIN `c12e422`: exact header names for Open Watcom; built as a COM
  program like the FreeDOS 1.4 binary.
- The lock records `upstream_package` (URL, zip hash, import commit); host
  tests check the import against its provenance record and that dropping
  the `__WATCOMC__` branches reproduces it. `EXE2BIN.LIC` carries the Sybase
  Open Watcom Public License.
- PC (FreeDOS 1.4 kernel) and VAEG VA2/640, VA/640: REPLACE replaces and,
  with `/A`, adds files (`/U` checked on PC); EXE2BIN converts a JWasm-built
  MZ to a COM that runs. Regressions of the other utilities pass on VA2/640.
- Utilities D88 `c6f360f3381eed9970b273919d09b178b710bbc965ec0c1109dd679a9bb01b91`
  (system D88 unchanged).

Not ported, by owner decision (deferred):

- UNDELETE assumes 512-byte sectors and stops with "not 512" on other media;
  the PC-88VA disks use 1024-byte sectors. Supporting them would extend a
  raw-sector FAT writer beyond its upstream behavior.
- SWSUBST needs the SUPPL and msglib libraries and generated message files
  (the `msgcomp` tool and its output are not in the package) and rewrites the
  DOS CDS directly.

## Archiver disk: UNZIP, ZIP and GZIP

Owner-approved new repositories `nakatamaho/unzip`, `nakatamaho/zip` and
`nakatamaho/gzip` hold verbatim imports of the FreeDOS 1.4 archiver package
sources (inner `SOURCES.ZIP` committed extracted) with `PROVENANCE.md`. The
pinned sources are the import plus its provenance record, unmodified
(`baseline_check: unmodified-import`, host test). FreeDOS 1.4 shipped a
32-bit DJGPP UNZIP and a 32-bit UPX-packed ZIP, which do not run on the
V30; the archiver disk carries 16-bit 8086 builds:

- UNZIP 6.00 and ZIP 3.0: Info-ZIP `msdos/makefile.wat` 16-bit settings
  (large model, `-s -oehiklrt`, assembler CRC and, for ZIP, match).
- GZIP 1.2.4: the Borland makefile's compact model with `DYN_ALLOC` (as
  `tailor.h` sets it for Turbo C); the TASM `match.asm` is replaced by the
  C code with `NO_ASM`.

`tools/m20/data_disks.py` generalizes the data disks: the producer,
two-build comparison, distribution verifier and source audit handle the
utility and archive disks by kind. `freedos-PC88VA-M20-ARC.D88` (label
`M20-ARC`) carries the three programs, `COPYING`, `UNZIP.LIC` and
`ZIP.LIC` (two Info-ZIP license versions) and a README.

Verification:

- HOST: host tests, two identical clean builds and acceptance pass. System
  and utilities D88 unchanged; archiver D88
  `9970958ca2dd5592f4231b4770b72c468e34deb967f0f0fd78c92eb97d61b913`.
- PC (FreeDOS 1.4 kernel): ZIP -r, UNZIP -t/-d and GZIP -9/-d -N round trips
  reproduce the original bytes.
- VAEG VA2/640 and VA/640 with the archiver D88 in B:: ZIP -r, UNZIP -t and
  -d, GZIP -9/-d round trips match; MEMMAP reports a valid MCB chain
  afterwards. Without `TZ`, UNZIP warns and returns 1 (upstream behavior);
  with `SET TZ=JST-9` it returns 0.
- VAEG VA2/512: all three exit cleanly with their out-of-memory messages
  (UNZIP/ZIP 4, GZIP 1). By owner decision the README states that the
  archivers need 640 KiB; no reduced-memory build is made.
- A first VAEG run of the D88 failed in the harness only (it called MEM,
  which M20 does not ship); its records are retained and the corrected
  harness was rerun.

## Archiver disk: DEBUG

By owner approval:

- `nakatamaho/DOS-debug` forks Baron-von-Riedesel/DOS-debug (FDOS/debug
  stops at 1.18 in 2010; the FreeDOS 1.4 package is this DEBUG) at
  `3d3655e`, the last commit before the FreeDOS 1.4 release (v2.50+1).
  `d0f149d` names `LINEASM.INC` by its file name (case-sensitive host);
  `95812fa` adds a `PC88VA` option that replaces the PC BIOS console use:
  INT 29h output (with TAB expansion) and a read request sent directly to
  the CON device driver (List of Lists + 0Ch) while DOS is busy and in the
  help pager, a 25-row pager instead of the BIOS data area, a beep through
  INT 29h and no video page query. The option is limited to the real-mode
  DOS program (assembly error otherwise).
- `pc_baseline.py` builds the fork without `PC88VA` and the upstream base
  (with the recorded `baseline_aliases` lower-case include copy) and
  requires equal bytes; both are `c4a6b987...`.
- The shared toolchain lock records a derived host tool: JWasm built by
  `make -f GccUnix.mak` from the pinned jwasm component inside the locked
  image, with its binary hash. The builder builds and checks it before
  assembling DEBUG as in its `MAKE.BAT`. `DEBUG.LIC` is Paul Vojta's MIT
  notice extracted from the source; Japheth's extensions are public domain.

Verification:

- HOST: host tests, PC baseline gate (kernel, FreeCOM, CHOICE, DELTREE,
  COMP and DEBUG), two identical clean builds and acceptance pass. System
  and utilities D88 unchanged; archiver D88
  `f17f7531cbfed9d9b34dca3a3020478860dbf89a1992061c7149b9e5901e2024`.
- VAEG VA2/640, VA/640 and VA2/512 with the archiver D88: the help pager,
  `R`, `A`, `D`, `U`, `N`/`RCX`/`W` (the written COM has the assembled
  bytes and prints its message), `G` with exit code 5.
- VAEG VA2/640 and VA/640, debugger entered while DOS is busy (an INT 28h
  handler executing INT 3 during a console read): the `!-` prompt, `R`, `D`
  and `E` read through the CON driver and echoed through INT 29h, `G`
  returns to DOS, and the program ends normally.
- Archiver checks rerun with this D88 on VA2/640, VA/640 and VA2/512 pass.
- Retained failed runs: two harness errors (an off-by-one in the test
  program's string address/length; one long script exceeding the driver's
  wall-clock limit) and two archiver runs that exceeded the limit with four
  emulators in parallel; DEBUG and the archivers behaved correctly in them,
  and the corrected runs above pass.

## Startup keys: kernel configuration read from the vector table

F5/F8 startup testing found a PC-88VA adapter defect. The PC88VA branch of
`kernel/main.c` copied `InitKernelConfig` from physical 0000:0002, the link
address of `_LowKernelConfig` relative to the kernel image; at run time the
image starts at `PC88VA_LOADSEG`, and physical 0000:0002 is the interrupt
vector table. `SkipConfigSeconds` was the low byte of the firmware INT 3
vector: on the VA2 the F5/F8 prompt waited about 41 seconds (unattended
boots continued only because the test scripts pressed Enter), on the VA it
was negative and F5/F8 were never offered. The drive-assignment, LBA,
boot-harddisk and version fields were vector bytes as well.

- fdkernel `9d2c3f6239028d87cda89224a5b0b9019d4d2a4e` copies from
  `&LowKernelConfig`, whose segment fixup follows the resident base (one
  more relocation, 492; INIT and layout sizes unchanged). The component test
  `test_m20_kernel_config_source.py` (run by the M20 gate) fails on the old
  source. The non-VA kernel still equals `ke2043` (PC baseline gate).
- The same code is in the stable M18 kernel (`e87e807`) and the M19 kernel
  (`2dba27f`, Preview 1). Those releases are unchanged; this is recorded
  here as a known issue of them.
- System D88 `4807a6942c06066eaeb0ecbfeb59743a375f98eed5b64db6917f796d590c0704`
  (utilities and archiver D88 unchanged).

VAEG (this disk):

- Register capture at `GetBiosKey`: timeout argument 2 on VA and VA2 (41
  before the fix on VA2; the VA never reached it before the fix).
- No key: on VA and VA2 the prompt is shown and cleared and the shell starts
  by frame 1000.
- VA/640 (the failing model): F5 skips CONFIG.SYS (`PATH=.`); F8 with N for
  `SET PATH` keeps the default `PATH=.`; shell, file write/readback and MCB
  checks pass.
- VA2/640: the same F5 and F8 checks pass with the key injected at frame 520
  through gdb, because VAEG's input harness cannot press a key before frame
  600 and the 1-2 second window then has already closed on the VA2.
- Regression controls pass: normal workload (JWASMR COM/MZ) VA2/640 and
  VA/640; reduced workload VA2 512 KiB with a retained 640 KiB selection,
  VA2/256 and VA/384; utilities disk VA2/640; DEBUG entered while DOS is
  busy VA2/640; archiver disk VA/640.
- Retained failed runs: F5/F8 scripts that pressed before or after the
  window (frames 300 to 1180 after the harness delay), an F8 "all Y" run
  that could not distinguish detection, and gdb harness runs that stalled or
  lost the last write when gdb killed the emulator (fixed by passing SIGTERM
  to it).

## Conventional memory: 256 and 384 KiB

With the default `PC88VA_LOADSEG=1000` and the M20 CONFIG.SYS, VAEG
results (VA2 and VA unless noted):

- 384 KiB: startup, MEMMAP, file write/readback and MCB checks pass; the
  whole utilities workload (FIND, SORT, XCOPY, MOVE, LABEL, DEVLOAD,
  NLSFUNC, APPEND) passes. JWASMR cannot start: DOS EXEC reports error 8
  because it needs about 330 KB (283 KB image plus 46 KB minimum) and about
  179 KB are free at the prompt. The system README already states that the
  sample assembly needs 640 KiB.
- 256 KiB: startup, MEMMAP, file write/readback and MCB checks pass; about
  48 KB are free at the prompt (the resident FreeCOM takes about 62 KB).
  DEVLOAD (COM), NLSFUNC, LABEL and APPEND run; XCOPY and MOVE are refused
  by DOS and SORT reports insufficient memory. These are resource limits,
  not layout faults.

## Repository organization

By owner decision the project repositories were transferred from the
`nakatamaho` account to the `FreeDOS-88VA` GitHub organization: the parent,
`fdkernel`, `freecom_dbcs2`, `JWasm`, `MS-DOS`, the utility forks (`choice`,
`deltree`, `comp`, `fc`, `attrib`, `tree`, `DOS-debug`) and the package
imports (`replace`, `exe2bin`, `swsubst`, `undelete`, `unzip`, `zip`,
`gzip`). Fork relationships, history, branches and tags are unchanged, and
GitHub redirects the old URLs. M20 references (`.gitmodules`, the M20 lock,
the M20 resolver policy, remote configuration, scaffold remote checks, disk
configuration text) use the new URLs; hash-pinned historical locks and
M01-M19 records keep the URLs they were made with.

The parent repository was then renamed `FreeDOS-88VA/freedos` (GitHub
redirects `freedos-pc88va`), and the organization profile README lives in
`FreeDOS-88VA/.github`.

The M20 kernel moved to `FreeDOS-88VA/kernel`, a GitHub fork of `FDOS/kernel`
(the former `fdkernel` is a fork of `lpproj/fdkernel` and keeps the M18 and
M19 history that historical locks reference). The commit is unchanged
(`9d2c3f6`), only the repository, `.gitmodules` branch (`m20/pc88va`) and M20
lock URL changed; the scaffold lock keeps its hash-pinned historical URL and
branch.

The M20 shell moved the same way to `FreeDOS-88VA/freecom`, a fork of
`FDOS/freecom` (the former `freecom_dbcs2` is a fork of `lpproj/freecom_dbcs2`);
commit `18b692a` is unchanged and the scaffold lock keeps its historical URL.

Japanese support is deferred to the next milestone by owner decision.

Known unrelated failure: `tests/qa/test_verify_license_policy.py` rejects the
tracked M17-M20 `CONFIG.SYS` files under its older generated-file policy; it
fails identically before this change and is not part of the M20 gate.

## Unrun gates

Not yet run: hardware (**NOT RUN**); PC regression beyond the scratch boot
smoke tests. Japanese support is next-milestone scope. No M20 distribution is designated.
