# M20 report: restart on the FreeDOS 1.4 release baseline

Status: **IN PROGRESS — kernel restarted on FreeDOS 1.4 and booting on VAEG;
FreeCOM still on its interim M19 pin.** No M20 distribution is designated.
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

## Kernel on the FreeDOS 1.4 baseline (local, not yet pushed)

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
instance inside the build. Not yet a published checkpoint: component and
parent commits are local, so no native CI or fresh public rebuild has run.

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

## Unrun gates

Not yet run: FreeCOM rebase onto `com086`; push of component branches and the
parent; native CI; fresh public clean rebuild; 256/384 KiB and other RAM
matrix entries; F5/F8 startup paths; PC regression beyond the scratch boot
smoke test. Hardware: **NOT RUN**. No M20 distribution is designated. No M20 image exists. Hardware: **NOT RUN**.
