# M19 work report

## Experimental VA kswap verification (in progress)

START_SHA: `ba868e2e33447fe5fcb3a2bed0711464f7968d82`, fetched from
`fix/m19-shell-startup`; its bounded report-only diff and source/scaffold CI
were verified before starting. This new parent branch is
`experiment/m19-kswap-va`; it does not change the published shell-preview tag
or the normal release branch. The pinned FreeCOM VA experiment is
`b334f316988f714086b47a3cabb336fe7e8a8145`, with independently requalified
child-status decoding and an explicit 8086 instruction boundary, descending
from config-only VA experiment `fbf735f63ceb3e263adad5c210904321c1c605c7`.
Component source
remains in its public fork and was pushed before the parent gitlink update.

The complete M19-local build now produces the matched KSSF/COMMAND pair and
component-owned original test fixtures. `tools/m19/qa/kswap_media.py` composes
separate fresh `/E:512` and `/E:8192` QA disks after two entire normal builds.
`kswap_readback.py`, host negatives and the committed guest-input script require
state preservation, twenty stable swaps, relocated MZ exit 7, normal guest
COM/MZ assembly/execution and settled MCB/file checks. The producer/verifier
and usage instructions are public source inputs, not private helpers.

The first complete clean two-build and fresh public two-build agreed; 116
parent host tests, isolation/source audit, linked placement and native source
CI `37113751126`, attempt 1, passed on implementation
`8cdbdf5ed2f29fcc140c4d54891998a19d6ed3d0`. VA2/640 KiB started and completed
all settled file/state/MCB checks, but its final screen exposed a remaining
status-decoding defect: a successful child exit 7 was passed as EXEC error 7,
producing an erroneous diagnostic. The same fallback was present in retained
PC screens; earlier file/return-code gates did not reject it. This first VA
candidate is therefore **not qualified**, and alternate RAM/model runs were
not substituted for a source fix. Its disk and evidence remain retained.

Common repair `52dd9a9af1048ceecd147e100c740c9d3f9b2c70` separates DOS EXEC
API errors from full AH=4Dh child status, preserving termination reasons and
using the ordinary decoder after context/resource setup. Independent PC
requalification passed two complete clean builds, all three runtime cases and
strengthened screen/decoder tests. Exact-head PC regression CI `37114741339`
and full build/test CI `37114741324`, both attempt 1, succeeded before VA
integration. The screen gate now rejects
`String #`/corruption diagnostics even when all files and return codes exist.
The matched status-correction VA rebuild also passed public clean build and
native source CI `37115623416`, attempt 1, on
`1473fe6674684efd704059813ac63df8548fd516`, but its VA2/640 KiB reload failed
the strengthened gate. Code growth crossed the signed-byte branch range;
unconstrained NASM emitted a 386 near conditional for `jne mainloop`, which
is not a V30-compatible reload instruction. This candidate is **not qualified**.
The code bytes/disassembly are reproducible public build outputs, not firmware
observations. Component `fd2b3eb5586ac94ec7624742497ac6ecd5c4926c` explicitly
sets `CPU 8086`; its host regression assembles the actual reload span, checks
the inverted-short/near-jump expansion, and proves the unconstrained span
would still emit a 386 opcode. The first dispatched CPU-regression CI `37116539915` failed because its host
NASM dependency was absent; it did not reach runtime and is retained as failed.
The explicit host-tool recipe correction is
`b334f316988f714086b47a3cabb336fe7e8a8145`. Its nine host tests, two complete
clean PC builds and all three PC runtime cases passed. Exact-head dedicated
CI `37116808065` and full build/test/cross-build CI `37116808110`, attempt 1,
succeeded before the updated VA pin/rebuild. Fresh public source archive
identity also agrees. Both failed VA candidates and their evidence are retained.

At `90d50e163f3f9c7397f084d75262aa363cffde4b`, 117 parent tests, two complete
clean local builds, a fresh public two-build, distribution/source/isolation and
linked placement verification passed; exact-head M19 CI `37117632849`, attempt
1, succeeded. VA2/640 `/E:512`, VA/640 `/E:512`, and VA2/640 `/E:8192` completed
the initial full workflow without the former status or ISA diagnostics. The
installed-512/retained-640 control started and completed its swap/state probes,
but ordinary JWasm exhausted its available DOS arena, so the full workflow
correctly failed guest source assembly. Its failing artifacts are retained;
this is not a full 512-KiB workflow PASS or a RAM-detection failure.

A targeted same-model/capacity/retained-setting run demonstrated source COM/MZ
assembly through `CALL /S JWASMR`, followed by normal execution. The public
fixture now requests these assembler loans explicitly, records restored
numeric exit status rather than redirected compiler stdout, and checks
alias/environment/recent history after the large child returns. Installed RAM
and retained settings are not altered to hide the failed ordinary execution.
The complete updated workflow is now independently qualified at
`a30e9173179b7adeff6e3ddd37d74730f1e39006`:

- **HOST PASS**: 118 parent tests and nine component host tests; two complete
  clean builds and a separate fresh-public two-build agree; public instance,
  source/privacy audit, milestone isolation and linked placement pass. Exact
  M19 source CI `37119860461` and scaffold CI `37119860465`, attempt 1, succeeded
  on that implementation SHA. Kernel and loader bytes equal the earlier
  kernel-repair/preview checkpoint; no saved DOS executables are build inputs.
- **VAEG PASS**, bounded to unattended startup and the specified workflow:

  | Model | Installed RAM | Imported retained selection | Shell environment |
  | --- | --- | --- | --- |
  | VA2 | 640 KiB | no backup input | `/E:512` |
  | VA | 640 KiB | no backup input | `/E:512` |
  | VA2 | 512 KiB | 640 KiB, preserved before/after | `/E:512` |
  | VA2 | 640 KiB | no backup input | `/E:8192` |

  Each fresh run completes twenty stable probe swaps, gains the borrowed
  arena with no live COMMAND-named blocks, preserves arguments and selected
  environment/alias/history state, returns swapped MZ status 7, assembles both
  source programs through explicit JWasm loans (status 0), executes their
  resulting COM/MZ normally, preserves post-loan state/recent history and
  settles valid MCB accounting. Original payloads remain unchanged. Startup
  and final screens were reviewed independently; completed-input/settled
  readback results and exact private runtime identities are retained locally.
- **DEFERRED HARDWARE VALIDATION**: real hardware **NOT RUN**.

Reproduce with `tools/m19/qa/KSWAP.md`. The source-generated QA disks are
`KSWAP-E512.D88`, SHA-256
`6de01f5bf00b137a57c80a3248a5ce8ea95171b5453eb5052240cf3227ac38df`, and
`KSWAP-E8192.D88`, SHA-256
`b06997ea7654c697de43880a6317e42bb6ddbddeee666a588772bed23e7d0953`.
These are experimental test images, not a new designated milestone release.

VA OOM fallback `/E:32752`, secondary shells, swapped batch/pipes/redirection,
UMB, live environment relocation, failed-reload cleanup, Borland runtime,
abnormal child termination on VAEG, KSSF F8/F5 paths, 256/384-KiB profiles,
actual media-swap safety and unidentified legacy media remain **NOT RUN** or
unqualified. Host decoder tests cover termination reasons, not those runtime
paths. The failed ordinary 512-KiB assembler execution is not retroactively
called a pass; use the explicitly qualified loan path.

Historical workflow failures remain separate from M19 gates. In particular,
root-policy run `37115623415` fails its historical M04 predecessor-diff scope,
not this M19 license/source audit; no historical acceptance is rewritten.
The normal FreeCOM pin on `fix/m19-shell-startup`, released Preview tag/assets
and stable M18 distribution remain unchanged. This is a bounded experimental
work checkpoint, not normal-release replacement or milestone HANDOFF READY.
See `tools/m19/qa/KSWAP.md`. Previous PC results do not qualify VA.

## FreeCOM kswap resumed: bounded independent PC qualification

Parent work starts from the exact released shell-preview tip
`f5f73ae09ff2037aed75de71bd5be3c503462409`. No parent gitlink, normal VA
configuration, kernel or released image is changed. This is an owner-authorized
common-FreeCOM repair, not a claim that the upstream DOS baseline has changed.

The public FreeCOM fork branch `fix/kswap-state` is now qualified at
`f5512b5a1756768830b541a274ac48973c46de12` (source archive SHA-256
`38c6a980e6584e6cdc257de438c61da60dde01a279ce56ea2e2a3b18f197efd9`).
A fresh public fetch reproduced that exact archive identity. The OOM fallback
uses the resident `dos_write` helper rather than CRT `fputs`: release FreeCOM
uses handle-valued FILE pointers, so CRT stream operations do not match that
contract. The diagnostic stays independent of STRINGS loading and the shell
executes normally without swapping when its environment backup cannot grow.

**HOST PASS, bounded independent IBM-PC/Open Watcom 1.9/no-XMS regression:**

- Two complete clean container-export builds produced identical COMMAND,
  KSSF and test-program bytes. Six negative/package host tests passed.
- Public PC FreeDOS kernel 2043/QEMU controls passed `/E:512` and `/E:8192`,
  twenty consecutive COM swaps each, environment/alias/history/command-tail
  preservation, relocated MZ execution and child return code 7.
- The `/E:32752` severe-pressure control printed its required allocation
  warning, retained the shell, and completed two ordinary executions with
  stable allocation accounting and valid MCB topology. The previously failed
  diagnostic case is now closed for this tested configuration.
- Exact-head native CI `37112286094`, attempt 1, job `pc-kswap`, passed the
  same two-build and three-case verifier used locally.

The separate DOS NASM launch defect was in CI dependency extraction: the
public package has Unix-origin uppercase paths, which `unzip -L` leaves
uppercase. `-LL` now establishes the lowercase path the recipe expects;
an original synthetic ZIP regression executes the actual extraction command.
The DOS recipe resolves NASM through PATH and preflights `nasm.exe -v`.
This is still the DOS assembler, not a host-assembler substitution. Exact-head
legacy build/test CI `37112286102`, attempt 1, passed its DOS/GCC/Watcom build
and test job and all five Watcom cross-build jobs. Earlier failing runs and
the unsuccessful PATH-only attempt remain retained as failures.

This PC acceptance is revision-specific, not VA acceptance. Batch, pipe and
redirection of swapped commands remain unsupported; secondary-shell swapping,
Borland repaired runtime, UMB, live environment relocation and failed-reload
cleanup are NOT RUN. **VAEG: NOT RUN; hardware: NOT RUN** for repaired kswap.
No repaired VA disk, FreeCOM gitlink update, general compatibility or milestone
HANDOFF READY is claimed. Next: independently clean-build/qualify a VA
experimental KSSF/COMMAND pair before considering any normal-pin update.
The published MS-DOS 4 COMMAND Preview 1 is unchanged.

## F8 `/Y` compatibility follow-up (bounded qualification)

- START_SHA: `6b6e8520be69b1516d0a82f189a1b0681eb82996`.
- QUALIFIED_IMPLEMENTATION_SHA: `99cbd700a97c54f06ac0ca762e1cf41a4cdf93b5`.
- Microsoft fork: `e46d23b474f9406160a03c08dd4d931435f8781c`, branch
  `fix/m19-freedos-y-option`; archive identity is in the research source lock.

The owner confirmed F8 startup but requested removal of its invalid-switch
message. The FreeDOS profile now recognizes `/Y` as an explicit no-op hint.
CONFIG confirmations remain in the kernel; AUTOEXEC still executes normally.
This is not batch single-stepping. Unknown/malformed switches still diagnose
errors. Kernel and FreeCOM pins, kernel/loader bytes, and the complete normal
FreeCOM D88 are unchanged. At this shell checkpoint, independent kswap work was separate and paused;
its subsequent PC qualification is recorded above.

**HOST PASS:** two complete normal-plus-shell builds agree; a clean public,
allowlisted checkout repeated both builds with other milestones absent and
produced the same QA disk. All 111 parent tests passed, including the component
media-policy gates. New negative readback tests reject a `/Y` diagnostic,
missing option outputs, suppressed unknown-switch errors and altered `/C`
command text. Source/privacy audit, isolation and the public normal instance
passed. Historical settled readback still validates without claiming the new
option coverage. The original-profile COMMAND remains byte-identical to the
upstream control (SHA-256
`19ebe2e5a8e18ca5d447a3d1fc42c42e4942ff5f3ef50e39ab01374bb01d8ea9`).

Native source-QA run `37108753023`, attempt 1, and scaffold run `37108753036`,
at the exact qualified implementation, succeeded. The publication tip's own
CI and public rebuild are checked after push, separately from this report.
Historical workflow failures are not an all-workflows-green claim.

A fresh PC FreeDOS 2043/QEMU control accepted `/Y` and lowercase/repeated `/Y`,
preserved `/C ECHO /Y`, and diagnosed `/Z`, `/YY` and `/Y:1` before returning to
the parent. The first assembly attempt exceeded an 8086 short-branch range;
the committed conditional trampoline fixed it before the successful builds.
Incomplete DOS-host/control-harness attempts are retained, not counted as PASS.

**VAEG PASS, bounded to this new disk:** F8 on VA2/640 KiB, VA2/512 KiB with a
persisted 640-KiB selection, and VA/640 KiB; plus unattended startup on VA2/640
KiB. Except for the explicit stale case, no backup input was supplied. Every
run completed settled file/batch/pipe/child-shell checks, COM/MZ assembly and
execution, held-open idle I/O, and MCB validation. `YOPTIONS.BAT` verified the
positive and negative option cases above. Separate F8 screenshots for both
VA2 capacities show CONFIG confirmations and the shell prompt without
`Invalid switch`; a separate no-input capture confirms unattended startup.
Installed capacity and retained selection remain separately recorded.

New experimental `MSDOS4-QA.D88`: 1,331,888 bytes, SHA-256
`e8ef926311d4edaec58461c962ca774a3455e2479b131a9d457aca6422633785`.
Rebuild with `tools/m19/qa/MSDOS4.md` and the pinned public inputs. Earlier
candidates remain retained; the normal distribution is not replaced. Hardware
is NOT RUN / **DEFERRED HARDWARE VALIDATION**. Other startup/RAM combinations,
SYS transfer and general application compatibility are not inferred from these
runs. There is no milestone HANDOFF READY claim.

Earlier kernel checkpoint: the media-uncertainty repair has **HOST PASS** and the
bounded **VAEG PASS** recorded under "Unattended-startup repair qualification"
below. The earlier shell-only checkpoints retain their original scope and
kernel identity. The normal distribution is not replaced; hardware retesting
is **NOT RUN**, and this is not milestone HANDOFF READY.

## FreeCOM kswap follow-up (earlier independent attempts; historical)

The follow-up starts at the fetched, exact MS-DOS-shell publication tip
`6d4e2dda024d21d3a8380adfa8900201be3bfdcc`. At that starting checkpoint,
the normal FreeCOM build and qualified MS-DOS shell candidate were unchanged.
The independent kswap work did not alter parent component pins; the later
kernel startup repair is recorded separately below.

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
`4223a28b78d1b0f5393f5d06ccd12acdebb6ddf0`. No FreeCOM gitlink update from
that branch is integrated. Paired PC builds restored swapping, dynamic context and child return
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

## Separate MS-DOS 4 COMMAND experiment (earlier shell-only checkpoints)

**Historical startup failure follow-up: BLOCKED for general-use handover.** The owner
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
general-use replacement had not been offered at that checkpoint. Unattended
startup was still open there; the subsequent kernel repair below adds bounded
coverage. A hardware retest remains NOT RUN. Historical results retain their
original scope; they do not establish unrun startup paths.

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
  VAEG `--nowait`. A key pressed before the prompt avoids it. At that original
  checkpoint the cause was unidentified; the later media-uncertainty repair
  below supersedes the tentative keyboard-polling hypothesis.
- Conventional memory remains well below the NEC DOS of the same era for
  large programs; most of the remaining resident use is the FreeCOM code and
  the kernel. Investigations of an MIT-licensed MS-DOS 4.0 COMMAND.COM on the
  FreeDOS kernel and of the kernel resident breakdown are planned.
- Hardware: the JWASMR startup fix, the HELLO.ASM build and running HELLO.COM
  passed on a VA2 with 640 KiB (owner report). Blank-disk FORMAT, SYS and 77-cylinder boot are **NOT RUN**
  on hardware.

## Unattended-startup repair qualification

- START_SHA: `c2fdaee8fb5904a40214db99d020eba6dc60b84b`.
- QUALIFIED_IMPLEMENTATION_SHA: `086f3da3a80b311db8b2fb00ad5e52d3af531c8f`.
- Kernel: `2dba27f199b5748553143cec0568da8596210088`, public fork branch
  `fix/m19-media-uncertainty`; exact archive identity is in the component lock.
- Microsoft shell remains `04a52f29cc4f8cd3289cbc8b645f42d7cbe4ad5c`;
  the FreeCOM gitlink and its non-swapping configuration remain unchanged.

This follow-up changes the experimental branch's kernel pin. It does not
replace the previously offered or designated normal distribution. Source
review identified a VA adapter mismatch: uncertain firmware media status was
returned as confirmed change, causing the filesystem to mark open handles
stale. The adapter now requests immediate read-only revalidation. A matching
nonzero DOS volume serial and complete BPB preserve the binding; changed
identity/layout, failed probes and unidentified media retain conservative
handling. Explicit change/reformat is not suppressed. Non-VA FreeDOS behavior
and the existing common CONFIG reader's handling of read errors are unchanged.

**HOST PASS:** two complete clean normal-plus-shell builds agree. A clean,
publicly fetched allowlisted checkout, with other milestone directories absent,
repeated both complete builds and produced the identical QA disk. All 110 parent
host tests passed; their gate also invokes two new component driver/assembled-
FAR-ABI tests and nine existing media-lifetime tests. The regression rejects the preceding
kernel. Missing/corrupt idle-probe outputs are rejected. Historical F8 settled
readback also passes without claiming the newly added idle-I/O coverage.
Linked placement,
carrier unpacking/relocations, descriptor/version/dynamic-top fields, source
isolation, privacy audit and the public distribution instance passed.

Native CI run `37103982570`, attempt 1, tested the exact qualified implementation;
its `source-qa` job succeeded, including two builds and the unchanged original
Microsoft-profile control. Scaffold run `37103982579`, attempt 1, also succeeded.
Historical M01-M09 workflows remain failing; this is not an all-workflows-green
claim. The publication tip and its own CI are checked separately after push;
this report cannot contain its own commit identity.

**VAEG PASS, bounded to the corrected QA disk and these cases:**

| Model | Installed RAM | Retained selection input | Startup path |
| --- | --- | --- | --- |
| VA2 | 640 KiB | No backup input | Unattended, F8, F5 (separate runs) |
| VA | 640 KiB | No backup input | Unattended |
| VA2 | 512 KiB | Persisted 640 KiB | Unattended |

Every listed QA run completed file/batch/pipe/child-shell operations, the invalid
`/Y` child, COM/MZ assembly and execution, settled readback and MCB checks. Each
also assembled `IDLEIO.COM` from the committed `IDLEIO.ASM` using the freshly
built JWASMR, kept a reader and writer open across five DOS clock second
changes, verified the reader and completed the writer. Readback required its
success marker and exact before/after file contents. Separate no-input captures
confirmed shell startup before the first workflow key in all three RAM/model
cases. The retained selection/checksum was checked before and after the stale
case. A separate F8 capture showed CONFIG confirmations, the expected invalid
switch diagnostic, and the prompt; `/Y` is still not implemented.

A separate freshly built normal-FreeCOM control passed on VA2/640 KiB:
kernel startup without an early key, acknowledgement of FreeCOM's normal
date/time prompts, COM/MZ assembly/execution, file write/readback and MCB
validity. It is not a claim that those normal date/time prompts disappear.

Incomplete attempts remain retained and are not counted: an operator-stopped
long-wait run; shortened post-probe waits with missing command outputs; and a
normal-shell script that failed to acknowledge date/time prompts. Corrected
harness runs above required full settled readback. An initial public-rebuild
invocation correctly rejected an untracked log in the source root; moving its
output to ignored build storage and repeating the complete build passed.

Corrected experimental QA disk: `MSDOS4-QA.D88`, 1,331,888 bytes, SHA-256
`21eacf00217faf54d7489014fb96f1aa95d6d968d530f3a41bae34b0c375a127`.
Rebuild it using `tools/m19/qa/MSDOS4.md` at the qualified revision and pinned
public dependencies. It is a disposable-copy test candidate, not a designated
milestone distribution or qualified SYS-transfer shell.

Limits: DOS volume identity is not physical-medium identity; clones with the
same serial/BPB are indistinguishable by these fields. Legacy media without
identity can still invalidate an open handle on uncertainty. See the pinned
component's `pc88va/M19-MEDIA.md`. Actual media-swap safety retesting, other
startup/RAM combinations and hardware are **NOT RUN** for this candidate.
Hardware remains **DEFERRED HARDWARE VALIDATION**; the owner's earlier F5
startup observation is not a hardware result for this disk. No general DOS
compatibility, complete M19 acceptance or HANDOFF READY claim is made.

## Not run

HARDWARE PASS covers only JWASMR startup, the HELLO.ASM build and the HELLO.COM
run on a VA2 with 640 KiB; VA hardware, other capacities, blank
FORMAT, SYS, 77-cylinder boot and the remaining workflow are NOT RUN on
hardware. The historical M01-M09
workflows still fail on this branch as they already do on `main`; they are not
M19 gates. The milestone image archive, acceptance metadata and handoff are not
done.
