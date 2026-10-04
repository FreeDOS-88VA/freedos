# M20 report: restart on the FreeDOS 1.4 release baseline

Status: **STARTED — planning only.** No component source, build recipe, image
or qualification has changed in M20 yet. HOST, VAEG and hardware gates are
**NOT RUN** for M20.

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

## Unrun gates

First-pass inventory: done (`docs/porting/m20-inventory.md`,
`tools/m20/inventory.py`, `tests/m20/test_inventory.py`). Component
branches, builds, VAEG and hardware are **NOT RUN**. No M20 image exists. Hardware: **NOT RUN**.
