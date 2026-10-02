# M19 work report

## KSSF experiment (not the normal distribution)

The `experiment/m19-kswap` branch starts at
`5fe502d673eafc3f57f3a7e690a3d9704ed9f1c0` (fetched predecessor tip;
M19 build and scaffold CI succeeded on that exact head). Its bounded final
publication change is report-only. Component checkouts matched clean gitlinks.
The experiment enables existing FreeCOM kernel-swap support and builds the
upstream KSSF wrapper against the same generated context. No swap algorithm or
common DOS behavior is changed. The complete normal M19 build recipe is used,
with a separate output directory; no old disk or saved binary is an input.

Experiment status: **BLOCKED; do not use as a replacement disk**.
Implementation tested: `860c536b34234e1111337ee200d30a7f89f7d6ff`;
FreeCOM: `e9307705ba4cdcd5f51eac0559ebdc90ea5c2a00` (configuration only).
Two complete allowlist-only container builds produced identical D88 bytes;
all 101 host tests and the linked-placement and public-instance verifiers
passed. Source/privacy audit passed inside the clean exports (not the working
checkout, which contains excluded evidence). The pushed revision
`f06017d8e39584443e23fc3287deadad150a7ce8` was rebuilt twice from clean
exports and produced the exact same D88 as the tested implementation.
Native M19 CI run `37014730287`, attempt 1 (`isolated-build`), and scaffold
run `37014730254`, attempt 1 (`verify`), both succeeded on that exact head.
The scaffold's initially stale lock selector was corrected; historical
milestone workflows are not experiment gates. **HOST PASS** applies only to
these build/source checks, never to swapping or the auxiliary guest workflows.
VAEG shell startup and an ordinary MEMMAP command worked, but the
first interactive `CALL /S MEMMAP` stopped with memory-chain corruption.
No successful swap, shell reload, memory saving, COM/MZ swap execution or
JWASMR benefit is established. Alternate models/capacities, stale retained
settings and hardware were NOT RUN for this experiment. Exact emulator,
configuration, input, failing media and observations are retained privately.
The previous distribution is preserved unchanged. Stop the trial at this
blocker: SYS transfer and allocator QA media were not adapted to carry the
new wrapper and must not be used with this experimental CONFIG.SYS. Their
guest boot/functionality is NOT RUN and is not established by host CI.
The normal branch remains the usable checkpoint; this experiment is not a
milestone release or HANDOFF READY. A later report-only publication does not
qualify its own CI merely by citing the above implementation runs.

### Public-source blockers (existing upstream code, not repaired)

- `shell/init.c` calls `kswapRegister()` before applying `/E:` or the automatic
  environment resize. `shell/kswap.c` allocates the saved environment using
  the old size. `kswapMkStruc()` later copies the **current** environment size
  into that old allocation. The size assertion is disabled in a release build;
  there is no runtime resize or bounds-error return. An enlarged environment
  can therefore overwrite the following MCB. This source-level defect is
  consistent with the failed swap; it is not a new VA RAM-detection issue.
- `kswapRegister()` passes `(word)ctxt` as the registration segment.
  `suppl/portable.h` defines `_seg` as a FAR pointer for Watcom, unlike Turbo C's
  segment-pointer extension. Narrowing that pointer takes the offset, not the
  segment. A separate pinned OW 1.9 `wcc -0 -ms -os -s` diagnostic with
  `void far *p = MK_FP(0x1234, 0)` emitted `xor ax,ax; ret` for `(unsigned)p`,
  versus `mov ax,1234h; ret` for `FP_SEG(p)`. These are synthetic compiler-test
  constants, not guest-derived addresses. Thus registration has another
  independent portability blocker even if the environment overwrite is avoided.
- `kswapLoadStruc()` reads `dyn_ctxt`, but the selected tree has no writer of
  that field after its zero initializer. Context restoration also needs an
  upstream review; it was not qualified by this experiment.

The relevant `shell/kswap.c`, `suppl/portable.h` and `tools/kssf.asm` are
unchanged from upstream master `e24bd7eab62502b1dad4099539f418ac5bc5f278`;
the registration/resize ordering also predates the VA port. Per project policy,
do not repair those upstream defects as VA adapter work. Enabling the feature
alone is insufficient; a separately reviewed upstream solution is needed.
The historical results below apply only to the previous candidate, not KSSF.
No new milestone PASS or handoff is claimed. See `tools/m19/README.md` for
rebuilding and the explicit swap commands/limitations.

## Previous non-swapping checkpoint

Status: **VAEG PASS for the published M19 work checkpoint; HARDWARE PASS for
JWASMR startup, the HELLO.ASM build and HELLO.COM run on a VA2 with 640 KiB
(owner report, 2026-10-02); other
hardware items NOT RUN.**
The parent branch `topic/m19-memory-format-tools` and the component topic
branches listed below are pushed to the `nakatamaho` forks. A fresh clone of
the pushed parent revision rebuilt the complete disk twice with identical D88
bytes, and its M19 and scaffold CI workflows passed. The designated milestone
archive under `images/milestones/m19/` has not been created yet.

M19 starts from parent `main` `0c66cd8242cb2a751fa473a5704c606269ab28d0`
(released M18 plus queued M19 notes). The owner redefined the M19 scope for
this work: conventional-memory reduction, native 2HD floppy maintenance
(blank-media FORMAT, 77-cylinder media), MORE input fixes and the JWASMR
physical-hardware stop. SASI data-drive work is not part of this report.

## Scope and results

| Item | Change | Evidence |
| --- | --- | --- |
| Milestone-local tooling | `tools/m19`, `tests/m19`, `config/m19`, `manifests/m19-components.lock.json`, `m19-*` Make targets, copied from M18 plus the reviewed M18 audit fixes | Isolation check forbids M00-M18 runtime inputs; host suite passes |
| JWASMR stop before Usage on hardware | OW 1.9 `clibl.lib(init8087)` begins its x87 probe with `FWAIT; FNINIT`. On an 8086-class CPU without a coprocessor FWAIT waits on the TEST input. A project `x87id.asm` replaces that module and decides presence with no-WAIT `FNINIT`/`FNSTCW`; the build rejects a link that still contains `init8087` | Host tests; VAEG VA/VA2 assemble and run HELLO/MZDEMO. VAEG does not model the TEST input, so emulation could not show the fix. **HARDWARE PASS** (owner, VA2 with 640 KiB, M19 public checkpoint disk): JWASMR with no arguments shows Usage, HELLO.ASM assembles and HELLO.COM prints its message |
| FORMAT | Formats every track through INT 80h AH=03h (disk mode 23h), verifies every sector, marks unreadable data clusters bad, writes a fresh volume with a date/time serial; `/T:80` (default), `/T:77`, `/Q` metadata-only | Host fixtures; VAEG VA/VA2 formatted blank D88 media at 80 and 77 cylinders |
| CHKDSK/SYS | Accept 80- and 77-cylinder native 2HD and DOS 2.x short BPBs; SYS keeps the target BPB geometry and label; SYS verifies LOADER.BIN lands on the source extent before writing the boot sector | Host fixtures; VAEG VA/VA2 SYS to both geometries, then booted the outputs and wrote/read a file |
| 77-cylinder boot | fdkernel stage 2 accepts a BPB of fewer whole cylinders of the profile geometry and loads files from a volume shorter than the disk | fdkernel pc88va suite (331 + new tests); VAEG VA/VA2 boot of SYS-output 77-cylinder disks |
| INT 21h AH=38h case-map call | The upstream case-map service in HMA_TEXT NEAR-calls `DosUpChar`. In the VA medium-model build that C body is FAR and HMA_TEXT runs from a relocated copy, so a program calling the case-map pointer returned by AH=38h jumped to a meaningless offset and hung (VA port defect; FreeCOM never calls it). fdkernel now calls it FAR under PC88VA, and a static test rejects any NEAR call into C that is active in the VA build | fdkernel suite; VAEG VA2: a probe calling the case-map pointer hangs on the earlier checkpoint and returns on the fixed build |
| Redirected maintenance output | Tools bound media with INT 21h AH=32h, which forces a rebuild; the VA media-lifetime code then marks open files of that drive stale, so `CHKDSK A: > X.TXT` was empty (M18 issue #12). Binding now uses AH=36h | VAEG VA/VA2: `CHKDSK A: > X.TXT` and `SYS A: B: > S.TXT` contain their output |
| MORE | Keys come from DOS AH=06h, or from a raw CON handle when stdin is redirected/piped; ZF read via `intr()`; CR does not count as a column | VAEG VA/VA2: `TYPE README.TXT \| MORE` and `MORE < QUICKSTR.TXT` page and quit |
| Conventional memory | FreeCOM PC88VA configuration drops kernel swap, LOADHIGH, LOADFIX, MEMORY, FDDEBUG (long filenames and LFNFOR kept at the owner's request); FreeCOM heap patched to 3 KiB with its own `ptchsize`; `BUFFERS=4`; `PC88VA_LOADSEG` stays 1000h (owner decision A) | VAEG VA/VA2 640 KiB: FreeCOM 63,040 B (M18 70,096), system block 9,520 B (M18 13,696), idle largest block about 441 KiB (M18 430 KiB); LFNFOR and FOR checked |

`PC88VA_LOADSEG=1340h` was evaluated and kept out of the default for now
(owner decision): its expanded image overlaps the 256 KiB staging plan at
27000h and needs more than 256 KiB of RAM. The default stays 1000h.

## Component pins (pushed)

| Component | Branch | Commit |
| --- | --- | --- |
| fdkernel | `topic/m19-77-cylinder-loader` | see `manifests/m19-components.lock.json` |
| freecom | `topic/m19-pc88va-compact` | see lock |
| jwasm | `topic/m19-source-notice` (milestone-neutral banner) | see lock |
| country, edlin | unchanged M18 pins | see lock |

## Verification performed

- `make m19-host-tests`: all tests pass (101).
- fdkernel `pc88va/tests`: all pass, including new 77-cylinder volume and file
  tests.
- `make m19-disk`: two isolated clean builds produce identical D88 bytes for each
  candidate built during the work, including a fresh clone of the pushed
  parent revision (`make m19-allocator-qa` and `make m19-accept` pass there).
- GitHub Actions: "M19 isolated native 2HD source build" and "Scaffold
  validation" pass on the pushed branch.
- VAEG (private ROMs, `--no-bkupmem` unless noted), VA and VA2, on the D88
  rebuilt from the pushed revision: boot, MEMMAP,
  CHKDSK A:/B:, blank FORMAT (80 and 77), SYS, boot of SYS outputs with file
  write/readback, JWASMR COM and MZ builds and runs, MORE with pipe and `<`,
  MEMMAP /CHECK.
- Capacity controls on VA and VA2: installed 256 KiB (boot and MEMMAP valid),
  and installed 512 KiB with a retained 640 KiB selection (DOS manages 512 KiB;
  MEMMAP valid). At 512 KiB JWASMR still cannot start (needs about 330 KB; about
  315 KB free), as documented for M18.

## Open issues

- **CONFIG.SYS loop after the F5/F8 window (pre-existing, also in M18):** if the
  "Press F8 to trace or F5 to skip" wait ends by timeout, or a key arrives only
  after a long wait, CONFIG.SYS processing repeats `BUFFERS=` with "line
  overflow" errors indefinitely. It reproduces with the released M18 disk in
  VAEG `--nowait`. A key pressed before the prompt avoids it. Root cause not yet
  identified (suspect the PC88VA `GetBiosKey` INT 21h polling during INIT).
- Conventional memory remains well below the NEC DOS of the same era for
  large programs; most of the remaining resident use is the FreeCOM code and
  the kernel. Investigations of an MIT-licensed MS-DOS 4.0 COMMAND.COM on the
  FreeDOS kernel and of the kernel resident breakdown are planned.
- Hardware: the JWASMR startup fix, the HELLO.ASM build and running HELLO.COM
  passed on a VA2 with 640 KiB (owner report). Blank-disk FORMAT, SYS and 77-cylinder boot are **NOT RUN**
  on hardware.

## Not run

HARDWARE PASS covers only JWASMR startup, the HELLO.ASM build and the HELLO.COM
run on a VA2 with 640 KiB; VA hardware, other capacities, blank
FORMAT, SYS, 77-cylinder boot and the remaining workflow are NOT RUN on
hardware. The historical M01-M09
workflows still fail on this branch as they already do on `main`; they are not
M19 gates. The milestone image archive, acceptance metadata and handoff are not
done.
