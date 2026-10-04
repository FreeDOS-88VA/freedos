# M20 inventory: M19 component history against the FreeDOS 1.4 baseline

Status: first-pass review. No component source has changed. Every proposed
class below is a review proposal; each actual import still records its own
source, commit, class and reason when it is made.

## Method

`tools/m20/inventory.py` reads only component Git history. For each
non-merge commit in a range it reports touched-path areas (`pc88va`,
`pc98`, platform scaffolding, metadata, shared code), added/removed lines,
`PC88VA`/`NEC98`/`DBCS` selectors in added lines, and whether its stable
patch-id equals an official FDOS commit after the baseline. Reproduce with:

```
python3 -B tools/m20/inventory.py --repo components/fdkernel --base ke2043 \
  --tip c9ce245e0447003645adce47bd34960ae276d4bd --upstream upstream/master \
  --markdown build/m20-inventory/k-lp.md
python3 -B tools/m20/inventory.py --repo components/fdkernel \
  --base c9ce245e0447003645adce47bd34960ae276d4bd \
  --tip 2dba27f199b5748553143cec0568da8596210088 --upstream upstream/master \
  --markdown build/m20-inventory/k-va.md
python3 -B tools/m20/inventory.py --repo components/freecom --base com086 \
  --tip 62dfacb4a88ca0a2b5a2b9b9c2c8ad5f8c917699 --upstream upstream/master \
  --markdown build/m20-inventory/f-va.md
```

Remotes must follow the M20 roles (`tools/configure_component_remotes.sh`);
fetch `upstream` first. Generated per-commit tables stay under `build/`.
The FDOS `upstream/master` used for this pass was kernel `d6791ad` and
FreeCOM `04fc21a`.

Classes: `upstream-backport` (same patch as an official FDOS commit after
the baseline, or an FDOS ancestor), `pc88va-only`, `pc98-only`,
`platform-scaffolding` (`template/`, `ibmpc/` multi-platform build tree),
`meta-only`, and `touches-shared` (needs review).

## Kernel

M19 pin `2dba27f` = `ke2043` + lpproj range (to `c9ce245`) + VA range.

| Range | Non-merge commits | upstream-backport | pc98-only | platform | meta | touches-shared | pc88va-only |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lpproj (`ke2043..c9ce245`) | 323 | 45 | 241 | 5 | 6 | 26 | 0 |
| VA (`c9ce245..2dba27f`) | 135 | 0 | 1 | 0 | 4 | 67 | 63 |

There are also 19 merge commits in `ke2043..2dba27f`.

### Findings

1. **The VA kernel build does not compile `nec98/`.** `pc88va/makefile.m13.wc`
   builds the shared `kernel/` sources plus `pc88va/` adapters. The 241
   `pc98-only` commits and the `template/`/`ibmpc/` scaffolding are not VA
   inputs. Proposed class: PC-98 specific, not imported.
2. **Shared kernel code holds almost no PC-98 code.** At the M19 pin,
   `kernel/` and `hdr/` contain only 5 `NEC98` references (`hdr/dsk.h`,
   `hdr/version.h`, `hdr/mcb.h`). lpproj's shared DBCS code is guarded by
   `#if defined(DBCS)`, which the VA build does not define.
3. **The VA shared-code delta is largely independent of lpproj.** Applying
   the VA diff for shared files (`c9ce245..2dba27f` outside `pc88va/`,
   `nec98/`, docs and CI; 6,234 diff lines) to plain `ke2043` with three-way
   merge changed 38 files and left 7 conflict hunks in 5 files: `hdr/mcb.h`,
   `hdr/sft.h`, `hdr/version.h`, `kernel/config.c` (2), `kernel/main.c` (2).
   The inspected hunks are context clashes with lpproj `#elif defined(NEC98)`
   or neighboring lines. Textual application does not prove semantic
   independence; the first M20 VA build decides that.
4. **Big-sector support is required and missing from `ke2043`.** VA media
   uses 1024-byte sectors and the VA build sets `-DMAX_SEC_SIZE=1024
   -DBIG_SECTOR=1`. `ke2043` has no `BIG_SECTOR` code. lpproj `d1e1ead`
   ("Add big sector support (larger than 512bytes per sector) for block
   devices") supplies it and is not in FDOS. Proposed class: shared platform
   infrastructure needed by PC-88VA.
5. 45 lpproj commits are exact cherry-picks of official FDOS commits after
   `ke2043` (released later in `ke2044`–`ke2046`). Under the 1.4 baseline
   they are not imported by default; import one only for a stated need, or
   receive them all through a later recorded upstream rebase.

### lpproj commits touching shared kernel code (proposal)

| Commit | Subject (abridged) | Proposed class | Proposal |
| --- | --- | --- | --- |
| `d1e1ead` | big sector support | shared infrastructure for VA | **import** |
| `b883d13` | merge freedos(98) diffs (mostly `nec98/`; `hdr` hunks NEC98-guarded) | PC-98 specific | no |
| `b937b16`, `9ce4074`, `dad60a2` | DBCS pathname support | DBCS (inactive without `DBCS`) | defer (Japanese support) |
| `070ef7f`, `e4c2be3`, `7fc0f48`, `e7b5f06` | Japanese/hard-coded NLS and NLS struct sizes | DBCS/NLS | defer |
| `5bbe4fe`, `88aeecb` | `NO_REVISION` / embedded revision sync | DBCS build option | no |
| `f342d33` | build master environment during FDCONFIG processing | adaptation of FDOS `3d1ba0d` (post-1.4) | no by default; `SET` already works in `ke2043` |
| `fcbfa55` | COUNTRY.SYS memory break in CONFIG.SYS | common fix | review if `COUNTRY=` is used |
| `780b013`, `363f5b8`, `9aa169e`, `16d690f`, `2cf05a7`, `526f819`, `e83ebfa` | INT 21h compatibility/workarounds (func 55h, huge device drivers, 5D06h, char devices, redirectors, INTERLNK) | common fix/behavior change | no unless a VA failure needs it |
| `e18ba52`, `da09863`, `18fdfb5` | Ctrl-Break/Ctrl-C checking, no INT 28h in INT 24h | common fix/behavior change | no unless needed |
| `a223935`, `d2bade8` | FDOS-author fixes (Int21.43FF, `current_ldt`) | common fix | no unless needed |
| `91bc589` | OW 2.0 warning in `dsk.c` | build | no (OW 1.9 is used) |

The VA range itself (63 `pc88va-only`, 67 `touches-shared`) is project work
to be re-applied in focused commits; its shared-file changes concentrate in
`kernel/asmsupt.asm`, `config.c`, `main.c`, `intr.asm`, `dsk.c`, `task.c`,
`entry.asm`, `kernel.asm`, `int2f.asm`, `memmgr.c`, `fatfs.c` and the
`sys/` tool.

## FreeCOM

M19 normal pin `62dfacb` = `com086` + 79 non-merge commits:

| Class | Commits |
| --- | --- |
| upstream-backport (FDOS after `com086`, through `e24bd7e`) | 37 |
| lpproj DBCS/NEC98 and project VA (`touches-shared`) | 41 |
| meta-only | 1 |

### Findings

1. **VA console support depends on lpproj platform hooks.** Cherry-picking
   the six VA commits onto plain `com086`: `6cd372b`, `9cf57b2`, `450d49b`
   and `62dfacb` apply cleanly; `855281a` (deterministic build timestamp)
   conflicts in `shell/ver.c`; `29bbbc7` (native PC-88VA console input)
   conflicts in all eight platform files: `build.sh`, `config.std`,
   `include/keys.h`, `include/misc.h`, `lib/cgetch.c`, `lib/cmdinput.c`,
   `lib/goxy.c`, `lib/xtra.c`. The platform selector (`build.sh pc88va`,
   `config.std` `__TARGET`) and the per-platform console hooks came mainly
   from lpproj `ab90394` ("import DBCS and NEC PC-98 support", +3,462/−122),
   which mixes platform hooks with DBCS. Proposal: backport only the
   platform-selection and console-hook parts as shared infrastructure for
   VA, recorded against `ab90394`; leave DBCS and PC-98 code paths out.
2. **The M19 Linux build may depend on post-0.86 official build fixes.**
   `com086` lacks `utilsc/` (host-native string tools), which the M19 recipe
   compiles with host `gcc`; FDOS added it in `d2fc51c` together with
   OW Linux/OW 1.9/cross-compile fixes (`88db97a`, `8d3dfd4`, `e18ffa2`,
   `4b4e451`, `acf0a2a` and related). First M20 experiment: build plain
   `com086` with the pinned OW 1.9 Linux toolchain; import the minimal
   upstream build fixes only if required (class: common fix, build only;
   `COMMAND.COM` behavior unchanged).
3. Other post-0.86 FDOS changes (version display, LOADHIGH/UMB, LFN probes,
   heap 6→8 KiB in `fa674ea`, `ptchsize` fix in `e24bd7e`) are not imported by
   default. The M19 recipe sets the heap with `ptchsize +3KB`; whether the
   `e24bd7e` tool fix is required is checked during the first build.
4. The repaired kernel-swap work (`fix/kswap-state`, `2e76de3..f5512b5`:
   5 code and 5 test/CI commits) is common code qualified only on PC; it is
   a separate later import candidate.

## Proposed first M20 steps

1. Kernel branch at `ke2043`: build the unmodified non-VA (IBM PC) kernel
   with the pinned toolchain as the baseline control.
2. Import `d1e1ead`, then the VA adapter and shared VA changes in focused
   commits, resolving the 7 known conflict hunks; build and boot on VAEG.
3. FreeCOM branch at `com086`: establish a pinned Linux build of the plain
   baseline (step 2 of the FreeCOM findings), then the platform-hook
   backport from `ab90394`, then the VA commits.
4. Only then create `tools/m20/` build/media orchestration and publish the
   first clean-buildable M20 checkpoint.
