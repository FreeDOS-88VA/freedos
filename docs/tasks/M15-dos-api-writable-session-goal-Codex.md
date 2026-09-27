# M15 completion goal: FreeDOS PC-88VA port and a usable writable session

Historical task notice (2026-09-27): the memory-sizing instructions below
belong to this milestone's recorded baseline. For active M16 maintenance, use
[the M16 memory contract](../porting/m16-memory-layout.md): measured writable
RAM replaces saved-selection sizing, and current LOADSEG/temporary-lifetime
rules apply. This notice does not change historical acceptance or source pins.

Revision: 2026-09-24

User scope amendment (2026-09-25): The goal is to port FreeDOS to PC-88VA, not
to fork FreeDOS into a separate DOS or implement MS-DOS compatibility. The
selected upstream FreeDOS source defines the DOS implementation being ported.
MS-DOS references are guidance only and do not require exact behavior matches.
Do not repair an existing upstream FreeDOS bug or change behavior solely to
match an MS-DOS reference. Fix VA-specific port or integration defects. Keep
the six MS-DOS reference questions linked to parent issues #3-#6 deferred; the
active FreeDOS services and any already recorded ordinary guest observations
remain in the inventory. The 221 inventory rows are dispatch-entry QA keys, not individual behavior
contracts. The historical V30 reference list bounds discovery only; required
behavior follows the pinned FreeDOS baseline and accepted VA integration. This
amendment supersedes conflicting language below.

Superseded user scope amendment (2026-09-24): the previous DOS 3.0 reference
boundary is retained as inventory history only. The 2026-09-25 owner amendment
below defines the current FreeDOS port scope.

Repository placement: `docs/tasks/M15-dos-api-writable-session-goal-Codex.md`
inside the active parent worktree selected for M15.

Invocation from that worktree:

```text
/goal Read docs/tasks/M15-dos-api-writable-session-goal-Codex.md in full and
complete M15 under its scope and acceptance rules. Verify the actual M14
baseline and preserve the current VA memory contract. Prioritize ordinary
supported-use QA. For a corner case absent from both the accepted specification
and current implementation, create a public issue in the parent freedos-pc88va
repository first; schedule it for M15 or later, after ordinary M15 QA. Complete
the API inventory, guest tests, evidence-supported repairs, writable FreeCOM
and batch sessions, SYS transfer, regressions, topic pushes/CI, and delivery of
the exact tested normal and transferred boot D88s. Report every 30 minutes.
Do not weaken acceptance, stop early, or start M16 before M15 passes.
```

## 0. Objective and authorized scope

Complete M15 of the revised FreeDOS PC-88VA roadmap. Qualify the supported
FreeDOS services and VA-specific integration through the actual resident
common kernel and VA device adapters. Demonstrate a usable writable session
in the real NECPC88VA FreeCOM, and create a bootable VA floppy through a
guest-executed system-transfer operation. Do not claim general MS-DOS
compatibility.

M14 qualifies FAT12 floppy writes, persistence, media changes, and focused
filesystem integration. M15 expands from that foundation to ordinary FreeDOS
process/resource, FCB, handle, redirection, batch, clock, and system-transfer
workflows. Reuse the common kernel and FreeCOM implementations. Repair defects
introduced by the VA port; preserve existing upstream FreeDOS behavior,
including known upstream bugs, unless the user explicitly changes this scope.

The user authorizes scoped implementation and repair in the kernel, VA adapters,
FreeCOM, an appropriate VA system-transfer utility, parent build/fixtures/
verifiers, and indispensable isolated VAEG work. Builds, tests, bounded analysis,
required regressions, records, task-owned commits, normal topic-branch pushes,
and applicable CI are part of this authority. Continue without asking again for
each ordinary implementation choice or internal phase transition.

This instruction supersedes earlier procedural limits that required stopping
at M14 or returning for approval after each diagnosis. Preserve earlier valid
technical contracts, historical evidence, privacy, and unrelated user work.
It does not authorize force-push, shared-history rewriting, merge to main,
unreviewed private-data publication, or writes to the user's original media.

Use English in code, comments, identifiers, committed documentation, test
messages, and technical reports. User-facing updates may be Japanese.

### 0.1. What comprehensive means here

Create an explicit inventory of the active target's DOS functions and
subfunctions. Every inventory row must have a justified disposition, and every
mandatory supported row must have meaningful execution evidence. A table with
only the calls that already pass is not comprehensive QA.

The target is the selected FreeDOS kernel and FreeCOM on the recorded VA
hardware/build profile, not a particular Microsoft DOS version. The locked API
inventory is a finite QA boundary, not an MS-DOS compatibility claim. Do not
infer compatibility from the version string: FreeDOS may report 5.2. DOS API
qualification also does not establish compatibility with IBM-PC programs that
directly use incompatible BIOS services or hardware.

### 0.1.1. Ordinary QA priority and post-M15 corner cases

Prioritize ordinary QA for supported VA DOS calls, real FreeCOM workflows,
and the guest SYS-transfer path before spending time on unusual input
combinations or speculative corner cases. A case is eligible for deferral only
when it is genuinely a corner case and evidence shows that it is absent from
both the accepted M15 specification and the current implementation. Verify
both absences from the active contract/primary references and source or call
paths; an uninvestigated behavior is not enough to qualify.

For each qualifying discovery, first create an issue in the parent
`freedos-pc88va` repository with an `[M15+]` title. State the precise trigger,
why it is outside the accepted M15 contract and ordinary supported workflows,
what source paths show it is not implemented, the user-visible risk, and a
recommended follow-up milestone. Use only public, non-private evidence in the
issue. Record its issue number/link in the M15 report and inventory as
`DEFERRED_M15_PLUS` with outcome `NOT_RUN`; count it separately from mandatory
M15 coverage. It is not a pass. Do not let it displace ordinary M15 QA; take it
up after that work if it fits the remaining M15 scope, or carry it to a later
milestone. If it is promoted into M15 mandatory scope, qualify it before M15
acceptance.

Do not use this deferral for behavior required by an ordinary supported
FreeDOS/VA workflow, documented errors encountered on supported calls, defects
introduced by the VA port, or a case whose status is merely unknown. Those
remain M15 work. For behavior inherited from FreeDOS, compare the VA build to
the pinned FreeDOS baseline and preserve its result; an MS-DOS reference does
not override it. When source and observed VA behavior differ, isolate the
port-specific change before deciding whether there is a defect.

The owner disposition dated 2026-09-25 explicitly defers the MS-DOS reference
questions in rows `21-1F`, `21-32`, `21-3A`, `21-63-AL_00`, `25-CXnot_FFFF`,
and `26-CXnot_FFFF` under existing parent issues #3-#6. This exception defers
only the disputed reference comparison. Keep these APIs in the active FreeDOS
inventory and preserve their recorded guest observations; do not turn them
into untested or excluded services.

### 0.2. Scope boundaries

M15 uses supported FAT12 floppy media, conventional memory, the existing
NECPC88VA target, and the current ASCII/8.3 baseline. Retain existing broader
common code without claiming qualification of configurations not exercised.

Do not start FAT16/FAT32 media qualification, HDD partitioning, SASI, SCSI,
MO, LFN, Japanese display/input/filenames, new EMS/XMS/HMA/UMB facilities,
network redirectors, multitasking, general printer/serial support, or a full
utility-distribution port. SASI boot is later; SCSI boot remains excluded;
MO remains at the end of the roadmap. M16 and later milestones are not part
of this invocation.

Inventory calls related to excluded capabilities and test their documented
unavailable behavior where meaningful. Do not enable those capabilities to
inflate coverage, or disable working common local services to avoid testing.

## 1. Resolve the actual baseline and preserve current work

Discover the active parent/component worktrees, branches, remotes, gitlinks,
dirty changes, toolchain, and current task state. Do not reset a checkout to a
historical SHA from another prompt. Use isolated task worktrees when appropriate
and snapshot task changes before editing. Preserve unrelated work and original
media.

Read root/scoped AGENTS.md files and current build, reproducibility, evidence,
CI, and acceptance instructions. Read the current M13 and M14 contracts/reports,
the M14 final or latest handoff, existing M15 records, and the latest VA memory
specification/status/handoff, including `docs/msdos211-memory-compat/` if present.
Earlier milestone numbers in old roadmap documents must not silently override
the revised scope in this instruction.

Record the actual parent/component revisions and dirty-source snapshot identity,
kernel, fully packaged COMMAND.COM, maps, compiler/linker configuration, VAEG
executable, model/ROM selection, launch command, and immutable boot/control D88.
Do not assume the prior M14 instruction proves M14 is complete.

Confirm the current M14 control with a focused sequence: normal boot, edited
command input, DIR/TYPE, COM/MZ execution and return, a known file write/reopen,
saved-image persistence, and the required media/protection behavior. Reuse valid
existing evidence; do not restart every historical investigation.

A bounded prerequisite regression may be repaired here and recorded as such.
If M14 remains substantially incomplete, prepare useful M15 inventories and
fixtures and identify the exact unsatisfied prerequisite. Do not label a missing
write/media subsystem M15 PASS or silently absorb an entire unfinished M14.

Keep the actual accepted VA-native memory sizing and ownership. Do not assume
640 KiB, reuse an old first-MCB address, reclaim an unexplained range, or introduce
IBM-compatible INT 12h / INT 15h/AH=88h shims. The separate memory work names
256/384/512/640 KiB settings; inspect its present qualification status rather
than assuming all four already work. Guest code uses the qualified mapped native
setting, not the emulator's host-side DAT file.

Use relevant local MD/TXT from `tekumani/`, `chip-databooks/`, and other actual
sources as needed.
NEC98 documents describe NEC98 assumptions, not VA equivalence. Missing original
PDFs are not a global blocker when the needed contract is available in text.

## 2. Phases and completion order

| Phase | Work | Required exit evidence |
| --- | --- | --- |
| M15a | Baseline, API inventory, FreeDOS/VA service profile, and reusable guest harness | Every discovered function/subfunction accounted for; expected behavior anchored to the pinned FreeDOS baseline and accepted VA integration |
| M15b | Console/device, handles, paths, FCBs, and disk-service conformance | Positive, negative, boundary, and state-transition cases pass through real DOS |
| M15c | Memory, PSP/EXEC/termination, vectors, errors, clock, and resource lifetime | Correct ABI/results and recovery without leaks or ownership violations |
| M15d | Writable FreeCOM, redirection, pipelines, batch, and startup session | Checked output/files/exit behavior; subsequent interactive commands work |
| M15e | VA floppy system transfer | A guest-created target disk boots independently and executes the accepted workload |
| Closure | Final regressions, coverage audit, publication, CI, and exact-image handoff | Final revisions, records, checks, and delivered artifacts agree |

These are internal work phases, not separate permission gates. A successful
inventory or diagnostic report is not the requested final outcome. Continue
through implementation and qualification. Parallel independent preparation is
allowed when it does not bypass a required runtime dependency.

## 3. Build a bounded API inventory for the FreeDOS port

### 3.0. Find the scope, cases, and current results

This goal document is the acceptance specification; it is not a linear
per-fixture run list. The finite API ledger, including each row's disposition,
case IDs, expected behavior, and `fixture_sources`, is
`config/m15/api-inventory.json`. The executable guest scenarios are under
`tests/m15/fixtures/`; host checks are under `tests/m15/test_*.py`. A fixture
may call additional DOS services to establish preconditions, so a row's case
IDs are not necessarily the complete record sequence emitted by that fixture.
Use `docs/porting/m15-report.md` for public aggregate progress and the excluded
`.private-evidence/m15/progress.md` for current run state. File presence or a
guest PASS message alone is not a qualified result.

Inspect the pinned local kernel's dispatch, headers, build guards, documentation,
and existing tests. Inspect FreeCOM's actual selected configuration and callers.
Enumerate INT 21h AH functions and relevant AL/AX or other subfunction values;
include alternate DOS entry paths and companion interrupts used by the active
profile. Do not guess packet layouts or call contracts from memory.

Use existing kernel/FreeCOM tests first. Record their revision, license, target
assumptions, original intent, and any adaptation. An IBM-PC-oriented harness
may need a VA launcher or output collector; do not change FreeDOS merely to
match an MS-DOS-only expectation. Add small original fixtures for ordinary
FreeDOS/VA workflow gaps rather than cloning a second DOS test framework.

For each row, record at least:

- Stable ID, interrupt/function/subfunction, and active build guard.
- FreeDOS behavior or relevant reference context; distinguish upstream behavior
  from VA-port requirements and record source locators where useful.
- Inputs, outputs, documented flags/register preservation, pointer/count units,
  side effects, and ownership/lifetime requirements.
- Applicability/disposition and a concrete reason.
- Positive, documented-error, relevant-boundary, and state-transition cases.
- Guest fixture/build identity, command, expected result, observed result,
  candidate/configuration identity, evidence path, and outcome.

Separate upstream FreeDOS behavior, VA-port implementation, and runtime
observation. Use primary references as context, but do not treat an MS-DOS
difference as a VA-port defect. Test ordinary target workflows and changes
introduced by the port; record upstream behavior without repairing unrelated
FreeDOS bugs. A test that derives its expected value from the same changed VA
routine merely repeats the implementation.

When comparison is useful and a suitable reference environment exists, run the
same portable guest fixture against an identified reference FreeDOS build or
another legitimately available DOS. Record version and environmental differences.
Differential agreement is supporting evidence, not the sole oracle. Do not make
proprietary MS-DOS media or a new IBM-PC emulator mandatory dependencies.

Use applicability such as REQUIRED, OUT_OF_PROFILE,
UNDOCUMENTED_OBSERVATION, or DEFERRED_M15_PLUS, separately from outcome PASS,
FAIL, NOT_RUN, or BLOCKED. `DEFERRED_M15_PLUS` is valid only under §0.1.1 and
requires the linked parent-repository issue. A documented unsupported call can
have a passing rejection test without counting as a supported feature. No
mandatory row may be reclassified merely because it fails. New discoveries
must be added with a reason; do not freeze an incomplete list to protect a score.

Report counts by both function/subfunction and behavioral test case. State the
denominator and list exclusions. Do not claim complete input-space testing or
substitute source line coverage for behavioral conformance.

## 4. Minimum DOS coverage families

The functions and subfunctions below are inventory leads, not a replacement for checking the
pinned ABI. Expand them for the actual implementation and accepted contract.
Do not silently omit a supported local service because it is not named here.

| Family | Inventory leads | Required semantic coverage |
| --- | --- | --- |
| Console and character input/output | INT 21h AH=01h,02h,06h-0Ch and standard-handle I/O | Blocking/status distinctions, echo, break policy, line counts, flush, EOF, redirected versus device input/output |
| Handle files | AH=3Ch-43h,45h,46h,57h,5Ah,5Bh,68h,6Ch where implemented | Access/create modes, read/write counts, seek, attributes/timestamps, duplication, inheritance, commit, and errors |
| Drives, directories, and search | AH=0Eh,19h,1Ah,2Fh,36h,39h-3Bh,47h,4Eh,4Fh,56h and other implemented drive queries | Drive/path state, DTA ownership, wildcard iteration, directory changes, rename, free space, invalid drive/path |
| FCB compatibility | AH=0Fh-17h,21h-24h,27h-29h and associated implemented services | Standard/extended FCBs, sequential/random/block records, file size, parse, wildcard search, create/rename/delete, DTA boundaries |
| Memory and process state | AH=48h-4Ah,58h and supported PSP/arena queries or setters | Paragraph units, allocation strategies, resize/failure semantics, MCB ownership, PSP/environment lifetime |
| Execute and terminate | AH=4Bh,4Ch,4Dh,31h; legacy termination entries where supported | COM/MZ load/relocation, command tails, nested execution, return status, cleanup, resident termination, supported overlay/load modes |
| Vectors and break/error handling | AH=25h,35h,33h,59h and INT 22h/23h/24h relationships | Pointer/return ABI, handler restoration, Ctrl-C/Break, extended error validity, allowed critical-error responses |
| Devices and disk control | AH=44h subfunctions, disk reset/verification state, INT 25h/26h when implemented | Character/block distinction, IOCTL contracts, valid rejection, absolute I/O ABI and cache coherence |
| Clock and date | AH=2Ah-2Dh and file timestamps | Get/set validation, progression, rollover, representation/rounding, independent directory persistence |
| System information and extensions | Version/break queries, supported country/codepage services, implemented multiplex entries | Truthful capability/version reporting, active ASCII behavior, documented unavailable-extension behavior |

Inventory related INT 20h/27h termination and supported INT 28h/29h/2Fh paths
at the boundary used by this target. Respect their distinct calling contexts;
do not treat every entry as an INT 21h call. Hardware interrupts and unused
third-party multiplex services do not become a new implementation mandate.

For legacy AUX/PRN services, SHARE/locking, network functions, or optional
extensions, state the existing capability and current scope explicitly. Exercise
local implemented semantics and correct unsupported behavior without claiming
unperformed peripheral or network validation. Basic resident-process lifetime
does not require adding a general TSR multitasking environment.

## 5. Guest harness and evidence integrity

Build fixtures for the accepted CPU/toolchain/memory model. Do not accidentally
link a 386-only runtime or IBM-PC BIOS helper into a supposedly portable DOS
test. Verify executable format, target selection, map, and packaged artifacts.

For direct API tests, use a small reviewed assembly wrapper where needed to
capture returned flags, registers, and stack state before C/runtime code changes
them. Preserve the test harness's own ABI. Distinguish defined outputs from
undefined/clobberable values. Check pointer validity, byte/paragraph/record
units, near/far parameters, and segment handling using the real contract.

Use guard bytes around valid buffers and inspect state before/after calls.
Do not demand modern memory protection for arbitrary invalid far pointers in
an unprotected DOS environment. Separate documented invalid-input cases from
undefined application misuse. Run intentionally disruptive cases in isolated
disposable guest sessions, with bounded output and restart information.

Tests must compute or compare results, return a checked failure code, and retain
case IDs and raw observations sufficient to diagnose a mismatch. A displayed
PASS string, a screenshot of a prompt, or an emulator process remaining alive
does not establish success. Do not force flags/results or inject expected output.

Avoid relying exclusively on the service under test to report its own failure.
For example, preserve an in-memory result record before risky file output and
use an existing approved observation path to collect it if needed. Test guest
memory writes made by the fixture are normal; host patches of guest state or
expected outcomes are not acceptance evidence.

Keep immutable fixture inputs and known expected payloads. Validate normal
filesystem results independently using the existing host FAT checker/parser,
then reopen the saved media in a fresh guest. Host tools may prepare/check
fixtures but must not perform the guest operations being qualified.

Every case has finite execution/time/output limits and a meaningful stop reason.
Keep event polling and guest progress live during frontend input automation.
Synthetic input must pass through the ordinary guest keyboard path; label it
automated, not manual physical typing.

## 6. M15b: files, FCBs, directories, and devices

### 6.1. Handle semantics and path state

Check create/open variants, access modes, existing/missing files, invalid handles,
read-only attributes/media, EOF, zero/nonzero lengths, seek from supported origins,
overwrite/extension/truncation, duplicate handles, forced duplication, and close.
Test same-file operations through independent opens versus duplicated handles
according to their documented file-position sharing and lifetime semantics.

Include independent stdin/stdout/stderr handles, redirection inheritance into
children, close-after-dup behavior, and exhausted/recovered handle capacity.
Verify open/inheritance flags supported by this kernel. Do not infer network
sharing guarantees when SHARE or a redirector is absent.

Exercise DOS zero-length-write semantics explicitly. Preserve M14's distinction
between valid short writes and errors: disk-full does not imply universal
all-or-nothing rollback. Compare returned status/count, file position/size,
allocated chain, data, and neighboring files.

Test absolute/relative and supported drive-relative paths, current directory,
root behavior, dot components, ASCII case handling, rename constraints, missing
parents, nonempty-directory removal, and supported path-length limits. Do not
substitute POSIX path or wildcard rules. Exercise FindFirst/FindNext with a
relocated DTA, no matches, end-of-search, attributes, and multiple independent
search contexts where supported. Ensure default DTA/command-tail overlap is
handled as documented, not mistaken for arbitrary corruption.

### 6.2. FCB semantics

FCBs are mandatory M15 coverage, not replaceable by handle tests. Cover standard
and extended FCB layout, default-drive handling, parse behavior, create/open/
close, sequential and random records, block transfers, file-size queries,
search iteration, rename, and delete using the actual supported calls.

Verify record-size and record-position arithmetic, partial final records, EOF,
DTA capacity, documented segment-boundary outcomes, status bytes/counts, and
state updates after success and failure. Do not reuse handle-I/O CF/error rules
for FCB calls without checking their ABI. Use a relocated guarded DTA and
neighboring-file controls. Reopen representative files through handle calls
to check common-filesystem agreement.

### 6.3. Devices, absolute disk I/O, and error visibility

Check CON/NUL and supported device information/status operations, handle versus
drive IOCTL subfunctions, raw/cooked modes where present, and well-defined
unsupported requests. Follow M13's non-destructive status/read semantics;
permanent not-ready or unconditional success is not a valid repair.

If absolute disk APIs are implemented or required by system transfer, check
their exact stack/flags/packet/count ABI with dedicated wrappers. Distinguish
logical-sector sizes from byte counts. Use only disposable exclusive test
media and the supported flush/revalidation protocol. Do not make raw writes
under a live FAT cache without establishing coherent ownership and invalidation.

Reuse M14's checks for write protection, unavailable media, full root/data,
bounded hardware error recovery, and A/B media exchanges. Verify DOS-visible
errors and subsequent operations. Old handles, retries, or dirty buffers must
not silently write to replacement media. Do not invent a media-change signal
or promise detection beyond the accepted hardware contract.

## 7. M15c: memory, processes, interrupts, and time

### 7.1. Memory allocation and ownership

Check allocate/free/resize with valid paragraph units, documented limits,
insufficient-memory returns, split/coalesce behavior, and supported allocation
strategy queries/changes. After both success and defined failures, inspect the
complete MCB chain and ownership without relying only on a free-byte total.
For resize failure, verify the actual documented post-call block state; do not
assume an unqualified transactional no-change guarantee.

Use the current accepted VA memory configurations. Test the main configuration
and the smallest qualified configuration capable of the workload, plus other
named gates required by the memory contract. Report resident/fixture overhead
and preserve arena ends/reservations. Do not hide loss by CONFIG.SYS tuning or
shrink the compatibility profile solely to make a large test harness fit.

Record resource state across repeated allocate/free and child-execution cycles.
Choose a finite count that exposes accumulation; compare owned blocks, largest
available block, handle state, and required persistent resources, allowing only
explained one-time initialization. Do not require byte-identical irrelevant
volatile state or run an unbounded stress loop.

### 7.2. PSP, EXEC, return, and resident lifetime

Exercise COM and relocatable MZ programs built for this target, including nested
execution, explicit command tails, environment inheritance, default FCBs where
specified, handle inheritance, child return codes, and parent resumption.
Cover missing/invalid executables and insufficient memory with a still-usable
parent and no leaked child allocations or handles.

Test the implemented EXEC subfunctions in the accepted local profile, including
load/overlay behavior when supported; do not count only the common load-and-run
case as coverage of the entire family. Inspect FAR parameter blocks and cleanup
using the actual ABI. Do not transplant a past RETF repair based only on similar
symptoms.

Check normal and supported legacy termination paths. Verify the documented
parent-state and INT 22h/23h/24h restoration rather than assuming every interrupt
vector is automatically restored. A child that hooks other vectors must restore
them itself unless it deliberately remains resident. Test bounded resident
termination with an original fixture and a fresh reboot afterward; do not
require implementing a new TSR scheduler or uninstaller.

Retain FreeCOM's working resident/transient arrangement and packaged resources.
Exercise a child that causes the existing supported transient reload path,
then another command, so a preserved prompt alone cannot hide broken reload.
Do not introduce unqualified disk swapping, XMS, or HMA to make EXEC fit.

### 7.3. Interrupt vectors, break, and critical errors

Test vector get/set with a controlled safe vector and restore original state.
Check far-pointer and return conventions. Do not hook a live hardware IRQ simply
to exercise an API wrapper.

Distinguish Ctrl-C/Break during line input, file/device operations, and a child.
Check INT 23h behavior and the active break setting. For INT 24h, exercise the
responses allowed by the actual request/context, especially recoverable retry,
fail, and abort-to-parent behavior. Do not force Ignore when the service forbids
it, or treat an ignored error as evidence that missing data was written.

Observe error code/class/action/locus only where the documented extended-error
state is valid. Capture it before unrelated calls can replace it. Prevent
recursive DOS logging from unsafe callbacks; use minimal reentrancy-safe
observation and report after returning to a safe context.

### 7.4. Date, time, and timestamps

Test get/set calls, valid/invalid values, time progression, supported calendar
rollovers, and file timestamp persistence. Derive representation and rounding
from the actual DOS/VA contract; directory timestamps need not have the same
resolution as a time-of-day API.

Use a disposable emulator configuration/persistence copy for guest clock-set
tests and restore or discard it afterward. Never change the host OS clock or
the user's normal emulator backup settings. Avoid unbounded waits until a real
midnight: use a supported guest/API or isolated emulator clock setup that still
exercises the real path, and label that setup. Do not patch returned guest time
values or accept a frozen clock.

Check that repeated clock/date calls and rollovers do not disturb disk I/O,
input polling, memory ownership, or child execution. Keep existing native clock
repairs intact unless new evidence demonstrates a specific defect.

## 8. M15d: practical writable FreeCOM and batch acceptance

Use the actual packaged NECPC88VA COMMAND.COM from the mounted disk. Verify its
source/configuration and full artifact identity, including appended resources.
Do not replace it with a fixture shell or enable IBMPC/NEC98 target code to
obtain superficially working command behavior.

Build a repeatable session that includes the following:

| Area | Required workload and check |
| --- | --- |
| File commands | COPY with supported binary/text modes, REN, DEL, MD/CD/RD, DIR and TYPE; compare actual data, names, and directory state |
| Standard streams | Input redirection, output overwrite and append, NUL, a child using standard handles, EOF and restoration of the parent's handles |
| Pipelines | A supported pipeline using existing commands or a small original DOS filter; verify bytes, child status behavior, temporary-file handling, and prompt recovery |
| Environment and lookup | SET/PATH, executable lookup, command tails/parameters, child environment inheritance, and scoped environment changes |
| Batch control | CALL/return, IF/ERRORLEVEL, GOTO, FOR, SHIFT, parameters/expansion, and nested batch behavior supported by the selected FreeCOM |
| Startup | The selected CONFIG.SYS/AUTOEXEC.BAT path, current drive/path/environment, and ordinary shell startup after a fresh boot |
| Failure and recovery | Invalid command/path, failed child launch, unwritable/full output target, break/abort, followed by a successful valid command |

Use exact syntax and semantics from the active FreeCOM. Do not import POSIX
pipeline concurrency, Windows command extensions, an unsupported stderr syntax,
or an equality interpretation of IF ERRORLEVEL without checking the contract.
Use distinct child exit values and assertions that distinguish the actual
condition semantics. A pipeline may use temporary files; qualify its existing
mechanism and error cleanup rather than demanding a Unix pipe implementation.

Keep binary payload comparisons separate from intentional text-mode conversion
or EOF conventions. Select an appropriate writable temporary directory/media,
record it, and test disk-full/write-protection there. Verify parent handles and
environment are restored after nested redirection and failed commands.

Existing built-in commands are part of this qualification. Use an original
small filter/helper when an external tool is not available; do not port an
entire utility collection just to test a shell pipeline. Do not use that helper
to bypass the real command parser or DOS operations being checked.

Run the integrated sequence from a fresh normal boot, verify saved disk content,
then reboot and execute another command/child against the saved result. Include
actual interactive editing through the ordinary frontend. Automated frontend
input is valid functional evidence but is not manual keyboard validation.

## 9. M15e: guest-driven VA floppy system transfer

Provide a supported way to make a prepared disposable VA FAT12 floppy bootable
from the running guest. Inspect the existing SYS utility and accepted VA loader/
packaging contracts first. Prefer a scoped VA backend of the maintained transfer
utility. If the project already has an equivalent guest utility, qualify that
path and document its command. A renamed host image builder is not equivalent.

Do not assume an IBM-PC 512-byte boot sector, INT 13h geometry, partition layout,
system-file placement rule, or PC-98 bootstrap works on VA. Derive the required
boot stages, reserved extents, sector sizes, file identities, and boot selection
from the current accepted VA loader and media contract. Reuse that loader;
do not redesign it just to match upstream SYS assumptions.

Scope is transfer to an already valid, supported FAT12 floppy image. Creating
an empty fixture on the host is allowed. A general FORMAT utility, low-level
track formatting, HDD partitioning, and a full OS installer are outside M15.

Required sequence:

1. Retain an immutable source boot/control disk and create a disposable target
   with a valid supported filesystem, known sentinel files, and no already
   functioning copied system that could conceal a failed transfer.
2. From the real guest FreeCOM, invoke the VA transfer command using the actual
   supported drive arrangement. If one-drive exchange is supported, specify
   its exact source/target identification and media-change protocol.
3. Transfer the required boot components and exact kernel/COMMAND.COM resources
   through guest DOS and qualified disk APIs. Preserve the target's required
   BPB/geometry and unrelated sentinel files. Check lengths and read-back.
4. Close/flush through the supported path, persist the image, and independently
   inspect boot extents, filesystem consistency, required files, and sentinels.
5. Start a fresh emulator with the transferred target as the only boot source;
   detach the old source disk or otherwise prove no fallback can use it.
6. Reach the real FreeCOM, perform DIR/TYPE and COM/MZ return, then create/write/
   reopen a file and verify it after a further saved-image reopen.

The installed image must be booted, not merely examined for filenames. Record
source, prepared target, post-transfer target, tested mount, and delivered bytes
separately. Do not clone a known-good D88 on the host and call that SYS success.

Exercise write-protected target, unsupported/mismatched geometry, inadequate
space/reserved layout, missing source component, wrong/source-equals-target
selection, and a meaningful interrupted transfer/error. Reject inappropriate
targets before mutation where the contract allows. Use positive target identity
and disposable media, not only an ambiguous drive letter.

Define safe ordering and truthful failure reporting. Preserve unrelated data
under the supported guarantees and never report successful installation after
an incomplete transfer. Do not promise power-loss atomicity or require a new
transactional filesystem. If the accepted loader exposes a genuine architectural
obstacle, prepare a concrete consultation and continue independent M15 tests;
do not silently replace guest transfer with host construction or omit this gate.

## 10. Acceptance matrix and failure rules

Reconcile the following minimum gates with the current accepted project
contract, retaining additional required gates and recording actual applicability.

| Gate | Required evidence |
| --- | --- |
| M15-BASE | Identified, qualified M14 candidate and preserved current memory/source contracts |
| M15-INVENTORY | Active FreeDOS services accounted for, explicit VA port profile, ordinary-workflow evidence, and honest coverage counts; no general MS-DOS compatibility claim |
| M15-ABI | FreeDOS port register, pointer/count, stack/segment, and buffer behavior recorded and checked for supported workflows; six disputed MS-DOS comparisons remain deferred |
| M15-CONSOLE | Character/line/status/flush/break and redirected I/O semantics pass |
| M15-HANDLES | File modes/counts/positions, duplication/inheritance, close/commit, metadata, errors, and recovery pass |
| M15-PATHS | Drive/path state, directory/search/DTA behavior, and invalid-path cases pass |
| M15-FCB | Required standard/extended FCB operations, record arithmetic, DTA, and error/EOF semantics pass |
| M15-MEMORY | Allocation/free/resize/strategy and MCB ownership/lifetime remain valid in required configurations |
| M15-PROCESS | COM/MZ, supported EXEC modes, PSP/environment, return codes, termination, and shell reload pass |
| M15-ERROR | Defined error/critical/break/vector paths recover and restore documented state |
| M15-DEVICE | Supported IOCTL/device and absolute disk services used by VA workflows operate through the FreeDOS port; disputed MS-DOS error-register comparisons remain deferred |
| M15-CLOCK | Date/time progression, setting/validation, relevant rollover, and persisted timestamps pass |
| M15-STREAMS | Real shell redirection/append/pipeline and parent-state restoration pass |
| M15-BATCH | Command/env/lookup/startup and nested batch/control-flow semantics pass |
| M15-SYS | Guest transfer creates an independently booted writable VA floppy and handles negative cases honestly |
| M15-LIFETIME | Finite repeated sessions show no unexplained handle, process-memory, vector, or temporary-file accumulation |
| M15-PERSIST | Successful writes and transferred-system data survive clean saved-image reopen/fresh boot |
| M15-REGRESS | Required earlier behavior and changed-component/public CI gates pass on the actual final candidate |
| M15-HANDOFF | Normal and transferred tested D88s, records, revisions, CI, commands, and delivered bytes agree |

All mandatory applicable gates must pass. Known failures, unexplained skips,
NOT_RUN, or unsupported mandatory behavior cannot be included in a full M15
PASS, except that a row meeting the narrow deferral rule in §0.1.1 is recorded
as `DEFERRED_M15_PLUS`/`NOT_RUN`, counted separately, and does not enter the
mandatory M15 denominator unless promoted into mandatory scope. Keep profile
exclusions and passing unsupported-call tests separate; never turn a deferred
row into a pass.
Changing a mandatory requirement requires a concrete decision, not editing a
golden until it matches the failure.

Hardware evidence is separate. Use `NOT RUN` or `DEFERRED HARDWARE VALIDATION`
unless actually tested; unprovided hardware alone does not prevent completing
all emulator-eligible work. Public CI, private VAEG acceptance, differential
reference tests, frontend automation, and manual operation have distinct claims.

## 11. Repair, regression, and emulator discipline

Trace each failure from the last correct producer/caller to the first incorrect
boundary. Distinguish a bad test expectation, harness fault, ABI defect, kernel
semantics, VA adapter, FreeCOM, transfer utility, and VAEG hardware behavior.
Do not restart boot-ROM analysis whenever a higher-level DOS call fails.

Make one explained logical repair at a time and check the original failure plus
affected earlier behavior. Prefer the common implementation's established
interface; do not encode a kernel bug into every application caller. Broad
architecture changes require consultation, while ordinary supported fixes are
already authorized.

Scope VAEG work to indispensable fixes/observability in an isolated checkout.
Separate diagnostic hooks from behavior changes. Behavioral changes need a
stated hardware contract, a distinguishing public/synthetic test when feasible,
the required production-memory/trace-on-off checks, and guest requalification.
Do not patch ROMs, fake BIOS compatibility, hardcode a private execution address,
or inject successful guest service returns.

Use focused checks during iteration and required complete gates for the final
candidate. Broaden testing only for an identified dependency or regression risk.
If common code changes affect IBMPC/NEC98 targets, run their required builds and
relevant tests, labelling build-only evidence honestly. Do not replace compiler
or dependency pins to evade a defect.

Keep every run bounded and check real exit statuses. Failed build/run/copy stages
must not reuse stale output. Prefer compact ordered observations to repeated
giant traces that miss the same boundary. Qualify normal production binaries
without private scripts/interposers; diagnostic-image success does not qualify
an untested normal rebuild.

## 12. Private evidence, persistent records, and publication

Use an excluded, persistent local evidence root for M15.
Keep immutable inputs, concise progress, API observations, failed-candidate
evidence needed for repairs, snapshots, manifests, and handoff outside temporary
storage. Reuse established repository record locations/schemas where equivalent.

Suggested disclosure-reviewed public records are:

- `docs/porting/m15-dos-api-profile.md`;
- `docs/porting/m15-dos-api-coverage.csv` or the existing machine-readable format;
- `docs/porting/m15-report.md`;
- original guest test sources and permitted synthetic fixtures;
- the existing active contract, status, manifest, golden, and verifier records.

These are suggested paths, not a requirement to duplicate an existing registry.
Private detailed records include `progress.md`, `acceptance.md`, identified
run directories, and `M15-consult-current.md` when needed. Public coverage records
may report permitted aggregate status; private locators/observations stay private.

Preserve the existing policy for manuals, ROM/D88 content, traces/disassembly,
and unpublished derived concrete values. Bounded read-only local analysis is
allowed when needed; distribution is a separate question. Do not leak private
facts through code constants, tests, commit messages, filenames, screenshots,
CI output, or external review requests. Public CI uses permitted public or
original synthetic inputs. Do not silently send material to Astra or any other
service.

If a required distributable implementation would introduce a new private-only
fact, prepare the exact local reviewable change and identify the disclosure
decision. Continue independent authorized work. Do not treat privacy as a ban
on local analysis or silently publish the value to make the milestone appear
complete. Preserve the root GPL-2.0-or-later policy and component/test licenses.

After local acceptance and scoped diff/privacy review, commit and push the
component topic branches first, then update parent gitlinks/locks and records,
commit/push the parent topic branch, and run applicable CI. Use normal pushes.
Fix actual CI failures; record transient service failures before justified retry.
Confirm checks correspond to the final behavioral revision or the repository's
explicitly permitted equivalent documentation-only revision.

Do not create an endless self-referential report-commit loop. Anchor tracked
results to a tested source/tree and put the final published tip/CI identifiers
in the durable local handoff, or follow the equivalent established workflow.
Completed work must not retain an implementation_in_progress contract.

## 13. Exact tested images and handoff

Deliver the handoff locally in the excluded persistent M15 evidence area,
using unique candidate names and preserving prior controls. Include:

- a qualified ordinary boot/session image;
- the exact guest-transferred target that was independently booted and
  qualified;
- necessary disposable fixture inputs/results and their reproducible recipes;
- SHA-256 sidecars and a manifest linking input, tested mount, persisted result,
  and delivered copies;
- a boot README and final handoff record.

If both image roles are genuinely the same qualified artifact, state that and
provide the identity once. Otherwise retain distinct identities. Do not attach
results from one image to another. Copy the tested bytes, compare sizes/full
SHA-256 values, and never rebuild after testing then silently deliver new bytes.

Keep private media paths, hashes, model/ROM configuration, raw observations, and
other private-derived values in the excluded local handoff. Public records and
messages may identify public source commits and CI runs, permitted aggregate
status, tested command sequences, and known limits; never publish private
inputs or their concrete derived values. Do not bundle ROMs.

Separate normal user boot from diagnostic commands, ordinary writable media
from deliberately full/fault-damaged fixtures, automated from manual input,
public CI from private guest acceptance, and emulator from hardware results.
Include the preserved media-exchange procedure and memory configurations tested.

## 14. Persistent progress and consultation

Update private progress after each meaningful experiment or repair: active
candidate/control identities, last correct/first unresolved boundary, current
hypothesis, next distinguishing action, completed/remaining cases, source
snapshot, tested images, and reproducible commands.

Report normally while working and save/present a checkpoint every 30 minutes
of active work. State what uncertainty was resolved or repair validated, current
blocker, next action, acceptance progress, and latest actually tested image.
Mark pending builds/CI as pending. A checkpoint is not a permission request,
a reason to end the task, or a promise of a timer after the session ends.

Prepare/update private `M15-consult-current.md` when:

- 60 minutes of active investigation produces no new discriminating evidence
  or runtime-validated repair for the current blocker;
- two evidence-supported repair attempts leave the same failure unexplained;
- the next proposal changes architecture, mandatory scope, compatibility
  semantics, or accepted memory/loader ownership;
- source, emitted code, and runtime observations remain contradictory.

More trace volume, unchanged rebuilds, or renaming a hypothesis does not reset
stagnation. A known build/CI wait is pending work. Consult earlier when the
decision is already clear enough to formulate.

The consultation contains one precise question, expected contract, last good/
first wrong boundary, ordered evidence, attempts and excluded hypotheses,
alternatives/tradeoffs, recommendation, identities/reproduction commands, and
work that can proceed independently. Preserve earlier consultations. Notify
the user with its persistent local path and a short permitted summary; do not
claim another reviewer has been consulted unless that actually happened.

Continue useful independent work while awaiting a decision; do not stack
speculative changes on the disputed path. If new evidence resolves the question
within the accepted design, record it, notify the user, and continue without
renewed permission. Do not repeat an unchanged question at every checkpoint.

## 15. Completion and justified interruption

Finish with `M15 PASS (VAEG)` only when the required FreeDOS VA port profile and
all applicable mandatory gates are qualified on the real common kernel and
NECPC88VA FreeCOM, the guest-transferred floppy independently boots and writes,
required regressions/public CI pass, records agree, intended topic pushes are
complete, and the exact tested images and reproducible fixtures are delivered.

Do not end after an inventory, a successful compilation, one API family, a
printed PASS marker, or a single writable session. Continue from discoveries
to supported repairs and final qualification. Do not weaken the profile to
turn untested or broken services into completion.

A final blocked handoff is justified by an indispensable unavailable input or
access, a denied necessary action with no safe alternative, a hard execution
limit, or a genuinely unresolved prerequisite after useful independent work
is exhausted. Use `M15 DECISION NEEDED` for a specific unresolved design or
contract decision on which all remaining useful work depends. Preserve the
exact question, recommendation/alternatives, restart state, and next command.
An ordinary unsolved code defect is not an external access failure.

Hardware remains separately qualified. Stop at M15 completion; record downstream
implications without starting M16, SASI/SCSI, language/LFN, or MO work.

## 16. Public reference leads

The active local fork and its pinned contracts are authoritative for build and
target selection. The following upstream projects provide reference leads:

- [FreeDOS kernel](https://github.com/FDOS/kernel): the repository exposes
  `test/`, `tests/`, and `sys/`; inspect the relevant local/pinned equivalents
  before adapting tests or system-transfer code.
- [FreeCOM](https://github.com/FDOS/freecom): the shell documents batch,
  redirection, and pipeline facilities and exposes a test directory; verify
  which features and tests are present in the selected VA fork/configuration.

These links do not prove the user's current checkout passes any test. Do not
switch to upstream master, assume its hardware target is VA, or replace local
accepted behavior merely because a newer upstream file differs.
