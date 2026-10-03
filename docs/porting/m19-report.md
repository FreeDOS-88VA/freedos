# M19 work report

## FreeCOM kswap follow-up (independent repair; paused)

The follow-up starts at the fetched, exact MS-DOS-shell publication tip
`6d4e2dda024d21d3a8380adfa8900201be3bfdcc`. Both the normal FreeCOM build
and the qualified MS-DOS shell candidate remain unchanged. No component pin,
kernel behavior or FreeCOM swapping implementation has been modified.

Public-release controls were run on PC FreeDOS kernel 2043 from the public
FreeDOS 1.4 floppy distribution, under QEMU with no extended-memory manager.
The shell line was `SHELL=A:\KSSF.COM A:\COMMAND.COM /E:512 /P`.
A DOS probe inspected the MCB chain from within an external command; it was
invoked normally, then with interactive `CALL /S` (not a batch or pipeline).

- FreeCOM 0.82 pl3 `binary.zip`: basic swap and shell reload occurred on two
  invocations, no live COMMAND-owned MCB remained while the swapped child ran,
  and an environment variable survived. The shell reported that its dynamic
  context was missing and recreated. This is not full state preservation or
  a VA qualification. The binary identifies the Turbo C++ runtime; the paired
  source defaults to Turbo C++ 1.01. An exact compiler archive and a fresh
  source rebuild of this historical release have NOT been qualified.
- FreeCOM 0.85a `bc/lang/bc-English.zip`: the Borland build booted and ran the
  ordinary probe, then halted with MCB corruption on its first swap request.
- FreeCOM 0.86 `English.zip`, `kswap/`: the Watcom build reproduced the same
  failure outside VA. Thus the issue is not solely a VA adapter defect or the
  current project's pin/configuration, and changing only the compiler is not
  sufficient.

The public archive root is
`https://www.ibiblio.org/pub/micro/pc-stuff/freedos/files/dos/command/`.
The selected release archive SHA-256 values are:

- `0.82pl3/binary.zip`: `970486a640eaa989814cd0c27bde88fd76ecf884330e9069c1fdd266f91d077c`
- `0.82pl3/com082pl3.zip`: `44de286e14c52dab5ae46c97c8026746589f603487fa99ce333557de1f919845`
- `0.85a/bc/lang/bc-English.zip`: `c4b7c78c4a497bd2a90d74ef4131f0f13c4a0e526f3e31b8c35818ba7fc81c54`
- `0.86/English.zip`: `42093a00286f66bf922eebd8204a3b74b429f4c6973cd960ae1ab52ce80b4bd5`

Source history identifies `1e600323d36c952572ce8141274e0a069adb0395`
(2004-06-29, `/LOW` change) as the change moving `kswapRegister()` ahead of
initial environment resizing. The old release performs that registration
later. This is a source-history finding, not a claim that this is the only
kswap defect. The Watcom segment-pointer registration and dynamic-context
ownership/lifetime still need separate review.

The owner authorized a separately scoped common-FreeCOM repair, not a VA
adapter change. The independent fork branch is `fix/kswap-state`, at published
`4223a28b78d1b0f5393f5d06ccd12acdebb6ddf0`. Normal component gitlinks are
unchanged. Paired PC builds restored swapping, dynamic context and child return
codes. The two positive environment-size cases each completed twenty repeated
COM swaps, retained state and executed the relocatable MZ. Qualification is
still **BLOCKED**: the severe-memory-pressure case reaches ordinary execution
but its required warning is missing. A working-tree correction uses FreeCOM's
resident DOS writer instead of CRT FILE operations and is not yet requalified.
The dedicated CI run `37081855346` failed that diagnostic gate. The separate
legacy build run `37081855340` also failed at its DOS NASM invocation; its five
cross-build jobs succeeded, which does not override either failure. This work
is paused for the owner's MS-DOS-shell startup failure report. New VA candidate
builds, VAEG kswap qualification and hardware are NOT RUN. Public binary controls are research inputs only, never
payload inputs to a new VA distribution. No new HOST PASS, VAEG PASS or
milestone HANDOFF READY is claimed. Diagnostic artifacts are retained in
Git-excluded research storage; generated files are not committed.

## Separate MS-DOS 4 COMMAND experiment

**Startup failure follow-up: BLOCKED for general-use handover.** The owner
reported startup failure with the offered QA disk on VA2 hardware and VAEG.
The emulator report includes CONFIG.SYS confirmation prompts, unlike the
previous early-Enter qualification. A fresh run of the same candidate on VA2
with F8 confirmation also failed to reach the shell; unattended startup
reproduced the previously recorded configuration-loop issue. Exact private
observations and failing media are retained separately. The precise owner
runtime identity and retained settings remain to be bound. The owner has
confirmed use of F8 on both platforms and separately reported shell startup
on hardware when bypassing configuration with F5; application execution and
file readback on that hardware path have not been reported. Do not
infer RAM exhaustion, a universal emulator PASS, or hardware success from the
prior runs. The F8 repair now has the bounded qualification below, but a
general-use replacement has not been offered. The unattended-startup issue
and a hardware retest remain open. Historical results retain their original
scope; they do not establish unrun startup paths.

Source review identified an additional shell-compatibility gap: FreeDOS
ignores the MS-DOS INT 2Fh/122Eh message-table registration interface, while
COMMAND uses it for resident parser diagnostics. The kernel adds `/Y` for
single-step startup, but this shell does not implement that switch. The
component implementation on `fix/m19-freedos-message-tables`,
`9de925dd732860655a43e5ad81b9d1c186450c0f`, keeps message pointers inside each
FreeDOS-profile shell instead of depending on kernel registration. It does
not implement `/Y` or alter kernel behavior. Standalone source builds for
original, FreeDOS and VA profiles completed; the original profile remains
byte-identical to the original-source control. An ordinary PC FreeDOS 2043
control reached its prompt with `/Y`, printed invalid-switch diagnostics,
ran a child with an invalid switch and returned to its parent. Interactive
COPY switch and child `/MSG` diagnostics also returned to the prompt.
The child repair and its documentation are now published at
`04a52f29cc4f8cd3289cbc8b645f42d7cbe4ad5c`; the experimental source lock
selects that commit. The normal kernel/FreeCOM gitlinks are unchanged.

### F8 repair qualification (general-use handover still blocked)

- Branch: `fix/m19-shell-startup`.
- Follow-up START_SHA: `6d4e2dda024d21d3a8380adfa8900201be3bfdcc`.
- QUALIFIED_IMPLEMENTATION_SHA: `044a39e1b235ffdaf1d63dd37a4b71d7f06f79e7`.
- **HOST PASS:** two complete normal-plus-shell clean builds agreed. A public
  sparse checkout of that exact revision, with historical milestone runtime
  directories absent and public component dependencies, repeated both full
  builds and reproduced the same disk. SHA-256:
  `c96fe6d5df30d925615cda0b8bfab417e7131b01ee5c53f9d12af2e7c201d93b`,
  1,331,888 bytes. All 108 host tests, linked-placement checks, isolation,
  source/privacy audit and public-instance validation passed. An initial host
  test invocation lacked Unicorn; the pinned dependency was installed in an
  isolated environment and the complete suite rerun successfully.
- Native source QA run `37099015309`, attempt 1, job `source-qa`, and scaffold
  run `37099015315` succeeded on the implementation SHA. Source QA includes
  the complete two-build recipe and original-profile/upstream byte comparison.
  The unrelated historical M03 run `37099015272` failed its obsolete component
  baseline check; this is not a claim that every repository workflow is green.
- **VAEG PASS, bounded:** F8 with CONFIG confirmation, shell startup, file and
  batch operations, child shells including the invalid `/Y` diagnostic path,
  JWASMR COM/MZ build and execution, settled disk readback, and before/after
  MCB validation. Controls covered VA and VA2 with the 640-KiB/no-backup-input
  configuration, plus VA2 with 512 KiB installed and a retained 640-KiB
  selection. The retained selection/checksum was checked before and after.
  VA2 early-Enter startup and the same workflow also passed. F8 startup was
  separately inspected on screen: `Invalid switch` is printed once and the
  shell prompt is reached. This does not add AUTOEXEC single-stepping.
- Early-screen-capture runs did not finish automated input and are retained
  as incomplete, not PASS. Qualification used separate startup captures and
  input-complete, settled-readback runs; the VAEG checkout was not changed.
- **DEFERRED HARDWARE VALIDATION:** corrected candidate hardware is **NOT RUN**.
  The owner's F5 startup observation applies to the earlier disk only.
  Unattended startup is not repaired or qualified. SYS transfer, general-use
  handover and milestone HANDOFF READY are not claimed. The normal component
  gitlinks and the earlier offered disk remain unchanged.

### Historical early-Enter qualification

The following describes the preceding publication, not a hardware pass or
universal startup acceptance.

Branch `experiment/m19-msdos4` starts from
`5fe502d673eafc3f57f3a7e690a3d9704ed9f1c0`, the clean, pushed normal
checkpoint. The owner scoped this task to running source-built MS-DOS 4
COMMAND.COM under VAEG on the unchanged FreeDOS kernel. The normal FreeCOM
image is preserved; the historical PASS statements below do not qualify the
new shell.

The original MASM 5.10 / LINK 3.65 build was reconstructed entirely from the
public Microsoft source/tool tree, generating all message classes afresh.
A normal PC FreeDOS control reproduced COPY failure: COMMAND requires OS/2
extended-attribute calls which FreeDOS does not provide. The optional shell
profile (separate Microsoft-source fork) omits those operations, accepts the
native FreeDOS version without a global VERSION override, and uses the VA DOS
console's native text-BIOS clear/home operation rather than IBM INT 10h for
CLS (DOS form feed alone was tested and did not clear the display). No FreeDOS kernel
behavior is changed. The adapted shell copied and read back a small text file
on the PC control. This is not a VA result.

Status: **HOST PASS; VAEG PASS for the bounded shell workflow below;
DEFERRED HARDWARE VALIDATION (hardware NOT RUN).** This is not a normal M19
release or milestone HANDOFF READY.

- START_SHA: `5fe502d673eafc3f57f3a7e690a3d9704ed9f1c0`.
- QUALIFIED_IMPLEMENTATION_SHA: `4b3bf7e80576b5fb66611452608e17fe0a952df5`.
- Microsoft-source fork: `825dc8753bf035835415ebf182c1b6ea786bfa64`;
  FreeDOS kernel and normal FreeCOM pins are unchanged.
- Two independent complete normal-plus-shell builds produced identical QA D88
  bytes: SHA-256 `fa8a3b3f0cd0f8837f0761274d174f0e7fd810995d941e188870368f9972fc4e`,
  1,331,888 bytes. All 107 host tests, linked-placement, isolation/privacy and
  public-instance checks passed. Failed intermediate builds/candidates were
  retained, not used as inputs. The original (no profile definitions) shell
  still builds byte-identically to the upstream Microsoft base.
- Native CI `M19 MS-DOS 4 shell source QA`, run `37025826401`, attempt 1,
  job `source-qa`, and scaffold run `37025826418`, attempt 1, job `verify`,
  succeeded on the exact qualified head. CI calls the same complete QA build
  and normal public-instance verifier as local testing, plus the original
  profile binary comparison. A later report-only publication must check its
  own CI separately; this report cannot contain its own publication SHA.
- VAEG: VA and VA2 with 640 KiB installed (no persisted backup input), plus
  VA2 with 512 KiB installed and a retained 640-KiB selection. On each exact
  candidate: startup, native-version VER, visible CLS and redirected CLS,
  COPY/TYPE/REN/DEL and missing-source rejection, FOR/IF, pipe to MORE, batch
  environment expansion, nested batch CALL, child COMMAND /C, JWASMR COM and
  relocatable MZ assembly/execution, and valid/stable post-batch MCB checks.
  Settled disk readback verified file bytes and all original media payloads;
  CLS screen captures were inspected separately. Exact emulator, disks,
  configuration, retained settings, input and results remain private.
- Normal MS-DOS 4 semantics are preserved: environment expansion is in the
  batch reader, not the interactive prompt; CALL does not retain a wrapper's
  redirection for every called command. The first test harness assumed newer
  shell behavior and was corrected, rather than changing the DOS parser.
- NOT RUN for this shell: hardware, VA at 512 KiB, a matching retained 512-KiB
  setting, other capacities, full editor/pager/maintenance regression, SYS
  transfer and arbitrary applications. The unchanged kernel's known F5/F8
  timeout issue remains; the scripts send early Enter, as in baseline tests.

Source pins and public acquisition/build instructions:
`config/m19/msdos4-research.json`, `tools/m19/qa/MSDOS4.md`.
Prior kswap research is parked separately, not an input to this build.

## Normal FreeCOM checkpoint (unchanged)

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
| Conventional memory | FreeCOM PC88VA configuration drops kernel swap, LOADHIGH, LOADFIX, MEMORY, FDDEBUG (long filenames and LFNFOR kept at the owner's request); FreeCOM heap patched to 3 KiB with its own `ptchsize`; `BUFFERS=4`; `PC88VA_LOADSEG` stays 1000h (owner decision A) | VAEG VA/VA2 640 KiB: FreeCOM 63,040 B (M18 70,096), system block 9,520 B (M18 13,696), increased idle largest block (earlier decimal-byte summaries were incorrectly labeled KiB); LFNFOR and FOR checked |

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
