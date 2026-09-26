# M14 completion goal: PC-88VA floppy writes and media changes

Revision: 2026-09-20

Repository placement: `docs/tasks/M14-floppy-write-media-change-goal-Codex.md`
inside the active parent worktree selected for M14.

Invocation from that worktree:

```text
/goal Read docs/tasks/M14-floppy-write-media-change-goal-Codex.md in full and complete M14 under its scope, acceptance, continuation, and consultation rules. Preserve the qualified M13 and current VA memory contracts. Continue through M14a, M14b, M14c, required regressions, records, topic pushes/CI, and delivery of the exact tested D88 and disposable media fixtures. Do not weaken acceptance or stop at an ordinary intermediate result. Do not start M15 or later milestones.
```

## 0. Goal, scope, and authority

Complete M14 of the revised FreeDOS PC-88VA roadmap: qualify FAT12 floppy
writing and media changes through the actual resident common FreeDOS kernel
and its VA block-device path, while preserving the working NECPC88VA FreeCOM.
Deliver the exact tested normal boot D88 and reproducible, disposable test-media
fixtures. Continue through implementation, runtime acceptance, records,
topic-branch commits/pushes, and applicable CI.

This is not a request to implement a separate FAT12 filesystem or emulate a
complete IBM-PC BIOS. Reuse the common kernel's existing filesystem code and
extend or repair the actual VA block-device integration at its owning boundary.

The revised roadmap controls this task's scope:

| Milestone | Boundary relevant to this instruction |
| --- | --- |
| M13 | Working VA FreeCOM, interactive editing, read-only DIR/TYPE, COM/MZ execution, and return to a usable prompt |
| M14 | FAT12 floppy writes, persistence, error recovery, media changes, and focused DOS filesystem integration QA |
| M15 | Comprehensive DOS API and writable-session conformance, including broader INT 21h coverage |
| Later storage milestones | Storage contracts, SASI data and boot, SCSI HDD data, and integrated storage qualification |
| Later language milestones | Japanese display/input/names and separately qualified LFN work |
| Final milestones | MO read/write and removable-media qualification, after the other planned work |

SCSI boot is outside the agreed roadmap. SASI boot belongs to later work.
Do not pull SASI, SCSI, MO, FAT16/FAT32, LFN, Japanese conversion, broad utility
porting, or a new installation system into M14. M14 is not an MS-DOS 2.11 API
ceiling: the existing FreeDOS kernel remains the implementation base. Preserve
the separate VA memory-compatibility work without making this task a restart
of that program.

The user authorizes evidence-supported M14 changes to the VA kernel/driver,
necessary narrowly related FreeCOM integration, parent build/fixtures/verifiers,
and indispensable scoped VAEG repairs. This includes ordinary dependency setup,
builds, targeted diagnostics, related regression fixes, acceptance records,
scoped commits, normal topic-branch pushes, and required CI. Do not ask again
for each already authorized step.

Earlier M13 read-only implementation limits and instructions not to start M14
do not forbid this explicitly requested M14 work. Their historical acceptance
records, input protection, privacy requirements, and valid technical contracts
still apply. Old diagnostic-only stop rules do not require stopping after a
discovery. Use section 13 for stagnation and design decisions.

Do not force-push, rewrite shared history, merge into a shared main branch,
overwrite user media, or publish private evidence. Keep source code, comments,
committed documentation, and technical reports in English. User-facing progress
may be Japanese.

## 1. Find and preserve the actual starting state

The normal repository root is `<repository-root>`. Discover the actual
active parent and component worktrees, branches, remotes, gitlinks, toolchain,
and task status. Do not assume the main checkout is the implementation worktree
or reset it to a historical SHA copied from an earlier prompt.

Read the applicable root/scoped AGENTS.md files and the current:

- M11/M12/M13 contracts, qualification records, manifests, and boot procedure;
- M13 FreeCOM NECPC88VA comparison/port report and final or latest handoff;
- milestone routing/status documents and existing M14 records, if any;
- build, reproducibility, public/private evidence, and CI instructions;
- VA memory specification, status, and handoff, including
  `docs/msdos211-memory-compat/` when present.

The user supplied the following documentation root:
`<repository-root>`.
Inventory relevant text with `rg --files`, then inspect `tekumani/`,
`chip-databooks/`, and the other directories only as needed. `nec98-databook/`
explains NEC98 assumptions; it does not define VA hardware. `pc-engine/` refers
to the VA operating system, not the game console. `goal-prompts/` contains task
history, not hardware specifications.

Use existing MD/TXT exports. Missing page images or PDFs do not block work when
the needed contract is supported by available text. Keep private locators and
distinguish source facts, documented specifications, runtime observations,
inferences, and unknowns. Never invent register values, OCR corrections, printed
page references, or firmware call semantics.

Before editing, record recoverable snapshots/focused diffs for dirty task work
and preserve unrelated files. Use isolated worktrees when needed; do not reset
or repurpose another user's working tree. Discover component paths from the
current parent, rather than assuming an extracted build directory is the source
of record.

Retain an immutable M13 control and identify its parent/component source state,
kernel, packaged COMMAND.COM, map, toolchain, VAEG executable/configuration,
ROM selection, boot D88, and launch command. Reuse valid evidence, but confirm
that the current candidate actually reaches the real shell and passes a short
M13 sequence: edited input, DIR, TYPE, controlled COM/MZ execution, return to
prompt, and another command.

Do not infer M13 PASS from a shell banner or this prompt's existence. If a
bounded prerequisite regression is found, identify and repair it before testing
dependent M14 behavior. If M13 remains substantially incomplete, prepare the
useful M14 contract/fixtures and a precise dependency handoff; do not conceal an
unfinished M13 port inside an M14 success claim or restart the entire port.

## 2. Preserve the latest accepted memory and ABI contracts

Keep the actual accepted VA-native memory sizing, reserved ranges, resident
kernel, loader lifetime, MCB chain, stack, and shell/child allocation contracts.
Do not assume 640 KiB, reclaim an unexplained gap, or allocate transfer buffers
in memory merely because a historical trace once found it unused.

The separate memory work uses the documented VA-native backup/common-memory
setting, with 256/384/512/640 KiB configurations. Read its actual current status:
these are not evidence that every capacity has already passed this build.
The guest must use the qualified mapped native information; it must not open
the emulator's host DAT file as a DOS file. Do not introduce IBM-compatible
INT 12h or INT 15h/AH=88h shims, invented fallback sizes, HMA/A20 assumptions,
or hardcoded old MCB addresses to make an M14 test pass.

Record the new driver's resident bytes, buffer sizes, and stack demand. For
the configurations qualified by the active memory contract, check that the
new layout and affected allocation paths remain valid. Exercise transfer-buffer
bounds at the smallest currently supported configuration that can run the
contracted workload. An unsupported configuration must be labelled accordingly,
not silently reclassified as a passing test or used to force unrelated memory
redesign.

Preserve established near/far calling conventions, request-pointer ownership,
register/flag preservation, segment assumptions, and interrupt entry/exit rules.
Verify emitted code where the ABI is in doubt. A segment-offset wrap and a
physical DMA boundary are distinct conditions; derive each applicable limit
from the actual VA transfer path and controller documentation. Do not import
an IBM-PC DMA wiring assumption from a similar chip name.

## 3. Work phases and contracts

Complete the phases in dependency order. A phase is an internal checkpoint,
not a routine reason to end the task.

| Phase | Work | Exit evidence |
| --- | --- | --- |
| Baseline | Qualify the current M13 control, memory ownership, driver contract, and disposable media harness | Identified working control and a concrete M14 acceptance matrix |
| M14a | Implement/qualify block writes, bounds, transfer splitting, and supported verification | Exact intended sectors changed; read path and memory remain valid |
| M14b | Qualify errors, bounded recovery, media changes, and cache invalidation | No false success or old-media writes to a replacement medium; subsequent valid I/O works |
| M14c | Exercise common-kernel FAT12 writes through real DOS services | Correct files/directories/FATs persist across close/flush and fresh boot |
| Closure | Run final regressions, reconcile records, push topic branches, run CI, and deliver images | Actual final candidate, records, CI, and delivered bytes agree |

Inspect the common kernel's block-device request definitions and dispatch in
the pinned source. Do not infer numeric command IDs, packet sizes, count fields,
status bits, or DOS error mappings from recollection. Trace at least write,
write-with-verification where supported, media check, BPB construction, read,
initialization, and any flush/invalidation operations actually used by this
driver and kernel.

For each path, record its caller, request layout, units, register/segment
contract, completed-count semantics, error mapping, retry ownership, and
relevant cache lifetime. Compare IBMPC and NEC98 implementations only where
they clarify common semantics or the port boundary. Retain the established
qualified VA read/firmware/controller path unless evidence requires a change.

Keep ownership clear:

- The block driver transports sectors, reports status, and participates in
  the real media-check contract.
- The common filesystem owns FAT, directory, file-size, and allocation logic.
- The existing DOS buffer layer owns its cache and flush/invalidation policy.
- VAEG implements hardware and image persistence; it must not manufacture DOS
  success or write expected filesystem contents on the guest's behalf.

Implement the smallest explained repair at the responsible layer. Do not create
a second filesystem, parallel cache, or private FreeCOM disk API to bypass a
demonstrated contract failure.

## 4. Disposable fixtures and trustworthy observations

Use a persistent private root such as:
`<repository-root>`.
Verify its Git exclusion. Preserve immutable inputs, controls, snapshots, concise
reports, final images, and reproducible commands outside temporary storage.

Build original synthetic FAT12 test media using the existing qualified fixture
tools. Derive sector sizes, geometry, BPB, cluster counts, FAT count, root layout,
and D88 representation from the actual fixture contract. Do not hardcode a
historical image size or assume a conventional PC geometry. Verify that each
fixture is actually FAT12 according to the implemented filesystem rules.

Keep an immutable boot/control image separate from disposable write fixtures.
Create distinguishable media A and B with known file content and legal differing
metadata; record their initial identities. Use supported drive arrangements.
If only one usable drive is available, design a coherent single-drive sequence;
do not require a second physical device that the user has not supplied.

Every mutating run starts with an identified disposable copy. Record source and
result paths, size, SHA-256, expected mutation set, launch/configuration identity,
guest commands, host exit statuses, and the result. Preserve failed candidates
needed to explain a repair. Never use the user's original D88, ROM, private
OS disk, or previously accepted handoff as the writable test target.

For block-level tests, compare parsed D88 track/sector structure, IDs, sector
headers, payload lengths, and payload bytes. Whole-file hashes identify images
but do not explain whether the correct sector changed. Allow only documented
container metadata updates; unexpected changes to geometry, protection state,
non-target payloads, or unrelated disk members are failures. If the container
can hold multiple members, explicitly identify the selected member.

For DOS-level tests, calculate expected files and structural invariants
independently of the guest's reported output. Use a trusted existing FAT checker
or a focused independent host parser to examine allocation chains, directory
entries, lengths, data, and all required FAT copies. A checker must detect a
deliberately corrupted disposable fixture relevant to the invariant being used;
do not build a large new validation framework merely for this task.

Separate raw-write tests from mounted filesystem tests. Run raw mutations only
on disposable media under an explicitly exclusive test arrangement, before
mounting through DOS or in a separate run that owns that device. Never issue raw
writes underneath a live DOS filesystem cache and then accept the resulting
incoherence as a driver defect. Test the production transfer code itself.

## 5. M14a: block writes and bounds

Implement the write path through the established VA interface. For each request,
validate unit, sector range, arithmetic, buffer coverage, and the actual command
contract before device access. Do not let a wrapped computation turn an invalid
large request into an apparently valid small one.

Check applicable sector/track/head transitions, device transfer limits, DMA
addressing/alignment, segment boundaries, and end-of-medium handling. Split
requests when required by the actual controller/firmware contract. Use a bounce
buffer only if justified by that contract and prove its bounds and ownership.

Track requested and completed counts using the actual DOS device semantics.
Do not report the requested count after a short hardware transfer or mark an
error complete merely because one earlier sector succeeded. A supported
write-with-verification request must perform the contract's real verification;
an unsupported operation must follow the documented unsupported-command policy.
Do not silently alias verification to unconditional success.

Required representative checks:

- Single-sector writes at the first and last valid positions of the test extent.
- Multi-sector writes spanning each materially different supported transfer
  boundary, including track/head transitions where applicable.
- Buffers close to actual segment and hardware transfer boundaries, with guards
  proving that unrelated memory is not overwritten.
- Invalid unit/range/count combinations, including arithmetic overflow cases,
  rejected according to the real contract without unintended device mutation.
- Zero-count behavior according to the device contract, not an invented policy.
- Read-back through the guest's production read path plus an independent
  post-run sector comparison.
- Verification behavior if that request is advertised or required by the
  current kernel's supported configuration.

Select valid, reachable boundary cases from the actual geometry. Record why an
inapplicable hardware limit is inapplicable; do not fabricate a device mode just
to fill a row. Check rejected requests leave their media and protected memory
unchanged. Do not impose that expectation on already partially completed writes
unless the contract actually provides it.

## 6. M14b: errors, recovery, and media identity

Use finite device waits and bounded retries. Establish the owner of each retry
so nested driver/kernel loops cannot silently create an unbounded wait. Preserve
the real timer/interrupt contract; host-speed busy-loop counts are not a
documented hardware timeout.

At minimum qualify write-protected media, missing/unavailable media, invalid
requests, and a deterministic lower-layer failure or timeout after work has
started. Include a failure after some progress when the path permits partial
completion. Observe status, completed count, memory guards, next valid request,
and actual media differences. Confirm that a DOS-visible error returns or
aborts the affected operation safely and leaves the shell usable.

Map controller/firmware outcomes through the actual device and DOS conventions.
Do not collapse every error into success or an unrelated constant. Check the
critical-error path needed by this workload, including its stack and reentrancy
rules; do not add diagnostic DOS calls from an unsafe callback. Broader INT 24h
and DOS API conformance belongs to M15, but a broken required M14 recovery path
must be repaired here.

Use normal emulator facilities and genuinely observed errors first. If a
mandatory failure cannot otherwise be exercised, a narrow deterministic test
hook at the hardware/controller boundary is allowed in an isolated emulator
worktree. Identify it explicitly; never patch guest requests, guest memory,
DOS return values, or expected outputs. Synthetic fault evidence does not
qualify the normal image's successful write path by itself.

### 6.1. Establish the actual change-detection contract

Determine how the VA path reports changed, unchanged, and unknown media, how
BPBs are revalidated, and how the common kernel invalidates its buffers and
open-file state. Use documented hardware/firmware behavior and identified
runtime observations. An emulator's host filename or test harness's knowledge
of a swap is not automatically a guest-visible change signal.

Do not promise automatic detection of a physical swap for which the supported
hardware exposes no usable signal. If detection is uncertain, follow a supported
conservative revalidation/error path. Record the supported exchange procedure
and actual limits. If the mandatory safety contract cannot be achieved through
the evidenced interface, prepare a concrete consultation; do not fabricate a
change bit or claim PASS with that mandatory row omitted.

### 6.2. Qualify clean and interrupted exchanges

Test at least:

1. Complete writes to A, close/flush using the real DOS path, exchange for B,
   and read B's own directory/data without stale A content.
2. Exchange with open handles or pending/dirty state at a controlled observable
   boundary. Old operations must fail, invalidate, or recover according to the
   established contract; they must not be silently retargeted to B.
3. Remove or replace media during a request or its retry/recovery window where
   the emulator/device permits this meaningful condition. Ensure late completion,
   retries, and cached writes for A do not mutate B.
4. Insert write-protected B after writable A. Protection and media state must
   be re-evaluated, not inherited from A.
5. Return to valid media and perform another successful supported operation,
   proving that recovery did not permanently wedge the controller or DOS.

Measure B against its immutable pre-exchange snapshot until an explicit new
operation valid for B is issued. Merely obtaining B's label in a later DIR is
not proof that no stale writes reached it. Do not replay old dirty buffers after
removal just because a new medium is ready.

## 7. M14c: FAT12 integration through actual DOS calls

Use small original guest COM/MZ fixtures and existing shell commands where
available. They must exercise the common kernel's normal DOS services and VA
block path. Verify returned status/counts and file contents; a printed PASS
marker without those checks is insufficient. Do not replace the guest workload
with host filesystem operations or hardcoded expected directory output.

Required workflows include:

- Create, write, close, reopen, and read a file with known binary data.
- Read/overwrite at nonzero offsets and extend across sectors and clusters.
- Rename and delete; verify that released clusters can be reused without
  cross-linking a surviving file.
- Create and remove a subdirectory, and perform a file operation inside it.
- Exercise zero-length files and the pinned DOS write API's zero-length-write
  semantics. Do not assume a zero-length DOS file write is always a no-op.
- Fill the fixed root-directory capacity independently of data-cluster capacity,
  then confirm correct failure/recovery without unrelated metadata damage.
- Fill available data clusters, observe the API's documented short-write or
  failure result, and compare reported count, final length, allocation, and data.
- Write/extend files whose allocation exercises adjacent even/odd FAT12 entries;
  verify updates preserve the neighboring entry's shared bits.
- Exercise a FAT12 entry that crosses a FAT-sector boundary when representable
  by a supported fixture. If the ordinary image is too small, use a legal larger
  supported fixture; if the geometry cannot represent it, record that exact
  limitation and the independent common-code coverage used instead.
- Verify every FAT copy required by the BPB and the common kernel's policy,
  directory structure, lengths, valid chain termination, and absence of
  unintended cross-links or leaked allocations after successful operations.

Derive file sizes and allocation sequences that actually hit these cases.
Large files alone do not prove an even/odd or sector-straddling FAT entry was
updated. Include unaffected neighboring files/entries as controls. For free
clusters, distinguish structural correctness from residual payload bytes;
deletion is not an implicit secure-erase contract.

Use a real close/flush/unmount or shutdown procedure supported by the DOS and
emulator path. Wait for image persistence before host inspection. Reopen the
saved result in a fresh emulator boot and verify files through DOS again.
Do not let an unqualified forced process kill stand in for a completed flush.

Do not promise transactional FAT12 behavior. A write that runs out of space may
legitimately be short according to the API; its result and metadata must agree.
An injected I/O interruption may leave partial data or metadata updates. Capture
and explain those results against the actual contract. Mandatory requirements
are truthful status/counts, bounded recovery, protection of unrelated media,
and the supported consistency guarantees, not invented all-or-nothing rollback
or power-failure atomicity. Unexplained normal-path corruption is always a failure.

## 8. Acceptance matrix and evidence rules

Create the current acceptance record before implementation, with case ID,
contract, input/candidate identity, expected result, execution command, observed
result, evidence path, and status. Reuse existing schemas rather than inventing
an incompatible reporting system.

| Gate | Required evidence |
| --- | --- |
| M14-BASE | Actual M13 boot/shell/COM/MZ control and current source/configuration identities |
| M14-MEM | Buffer/resident ownership, preserved accepted arena, ABI, and meaningful bounds checks |
| M14-BLOCK | Single/multi-sector writes and applicable geometry/buffer boundaries change only intended locations |
| M14-VERIFY | Correct implemented verification or explicit contract-supported non-support; no false success |
| M14-REJECT | Invalid requests fail without unexpected media/memory mutation |
| M14-PROTECT | Guest-observed write protection, absent-media behavior, and protected inputs remain intact |
| M14-ERROR | Deterministic failure/timeout and applicable partial completion have correct status/count and bounded recovery |
| M14-CHANGE | A/B exchanges revalidate media and prevent stale reads, old retries, and old dirty writes reaching B |
| M14-FILES | Actual DOS create/write/seek/read/rename/delete and subdirectory workflows pass |
| M14-FAT | FAT12 neighbor/boundary cases, required FAT copies, allocation, and directory invariants pass |
| M14-FULL | Root-full and data-full conditions follow the API and leave a usable system |
| M14-PERSIST | Closed/flushed changes survive saved-image reopen and a fresh guest boot |
| M14-SHELL | Real NECPC88VA FreeCOM remains usable after writes, errors, media exchange, and COM/MZ return |
| M14-REGRESS | Relevant earlier read/input/EXEC gates and changed-component requirements remain valid |
| M14-NORMAL | Normal build/launch writes without private patches, diagnostic-only dependencies, or fabricated services |
| M14-CLOSE | Verifiers, manifests, final source revisions, public CI, private results, and delivered artifacts agree |

Every required applicable gate must pass. NOT RUN, BLOCKED, and UNSUPPORTED are
not synonyms for PASS. A contract-supported non-applicable case needs a reason;
do not silently change applicability after it fails. Proposed removal of a
mandatory behavior requires consultation, not an acceptance-record edit.

Keep public synthetic tests, private VAEG acceptance, automated frontend input,
manual keyboard checks, and real-hardware evidence distinct. Hardware validation
remains NOT RUN or DEFERRED HARDWARE VALIDATION unless it actually occurs.
Unprovided hardware alone does not block emulator-eligible completion.

## 9. Regression scope and the historical read-only baseline

Preserve M12/M13 historical images, reports, and original qualification meaning.
The deliberate M14 transition permits writes to supported writable media.
An old test that expected every write to be rejected must not be applied
unchanged as a requirement of the writable M14 configuration.

Version the active capability/contract and scope old negative tests to their
historical read-only configuration where appropriate. Keep protection checks
for genuinely write-protected media and immutable inputs. Explain changed
expected behavior; do not erase old evidence or blindly refresh goldens.

During development, run focused tests that distinguish the defect and affected
boundary. At final qualification, run the required complete gates for changed
components and parent integration, including read-path and memory/ABI checks.
If common code changes can affect other targets, run their applicable compile
and meaningful regression gates. Do not claim hardware runtime coverage from a
successful cross-build.

Comprehensive INT 21h conformance is M15. M14 nevertheless must correctly test
the API subset that causes its actual writes, allocation, flushes, and recovery.
Do not defer a failure in a required M14 workflow merely because its entry point
is INT 21h. Conversely, do not start unrelated FCB, networking, broad batch,
NLS, or utility work just to enlarge the milestone.

## 10. Emulator, harness, and diagnostic discipline

Use the recorded accepted model, ROM selection, drive/configuration, frontend,
and production-memory build. Discover actual command syntax locally; do not
invent a launch option or substitute a different ROM to obtain a green result.

Run each emulator/test invocation with finite time, output, and capture bounds
and an explicit stop reason. Check exit statuses and timestamps/identities at
each build/run/copy stage. Failed stages must not reuse stale output as evidence.
Prefer targeted events, compact projections, and bounded ring traces to repeated
large traces that miss the same producer/consumer boundary.

Input automation must follow the normal frontend and guest keyboard path.
Keep event polling and emulation progress active while gating synthetic events.
Do not inject shell characters into guest buffers or force successful services.

Necessary VAEG changes are authorized in an isolated worktree. Separate
observability/test hooks from behavior changes. A behavior fix needs an expected
hardware contract, a distinguishing regression preferably using public synthetic
inputs, required production-memory checks, and affected guest requalification.
Do not patch ROMs, special-case a private boot PC, or fake media-change/status
results solely for this guest.

The final ordinary build must boot and write without a private interposer,
guest-state patch, or debug script. If diagnostic and normal binaries differ,
record both and qualify the normal candidate itself. Investigate behavior that
changes when tracing is disabled. Display concise progress only at safe
boundaries; do not add recursive console logging inside critical I/O paths.

## 11. Privacy, source control, and CI

Keep private manuals, ROMs, D88 contents, traces, disassembly, and unpublished
derived concrete values local under the existing evidence/promotion policy.
Bounded read-only private ROM/OS-media analysis is allowed when necessary to
resolve a documented interface gap; preserve originals. Privacy does not prohibit
that authorized local analysis.

Public tests/CI use permitted public or original synthetic inputs. Do not assume
that a D88 assembled from apparently public components is publishable without
checking its full provenance and the project's distribution policy. Keep the
tested handoff local by default. Do not leak private facts in commit messages,
filenames, screenshots, failing CI logs, or consultation summaries.

If a required implementation introduces a new private-only value into code
intended for publication, isolate and finish the reviewable local change, use
any valid already-public interface where appropriate, and raise the concrete
disclosure decision. Do not silently promote the value or claim public completion
while omitting required implementation.

Keep the accepted toolchain/dependency pins and reproducibility settings.
Preserve root GPL-2.0-or-later and all component/third-party license notices.
Do not replace dependencies just to evade a failing check.

After local acceptance and scoped diff/privacy review:

1. Commit only task-owned changes in their correct component repositories.
2. Push component topic branches normally before publishing parent gitlinks.
3. Update the parent locks/gitlinks and active contracts/manifests/records.
4. Commit/push the parent topic branch and run its applicable CI.
5. Verify that the required checks belong to the actual final code revision.

Fix real CI failures and continue. Record and retry transient service failures
without weakening checks. Use the existing documented policy for equivalent
documentation-only revisions, if one exists. A green run on an older behavioral
revision is not final validation.

Avoid a self-referential commit loop: a tracked report cannot contain the SHA
of its own future commit. Anchor tracked acceptance to the tested source/tree
and place final tip/CI identifiers in the durable local handoff, or use the
repository's established equivalent workflow. Do not leave completed contracts
marked implementation_in_progress.

## 12. Durable deliverables and exact image handoff

Reuse equivalent established record paths. Suggested records are:

- Public, disclosure-reviewed M14 contract/ADR, concise report, original test
  sources/fixtures, and the existing manifest/golden/verifier records.
- Private `progress.md`, `acceptance.md`, identified run directories, focused
  diffs/snapshots, and `M14-consult-current.md` when consultation is needed.
- Private handoff under
  `<repository-root>`.

Deliver uniquely named files such as:

- `M14-accepted-<candidate-id>.d88`: exact qualified ordinary boot image;
- disposable fixture inputs A/B and the relevant resulting written image(s);
- SHA-256 sidecars and a manifest connecting input, tested mount, saved result,
  and delivered copies;
- `M14-BOOT-README-<candidate-id>.md`;
- `M14-final-handoff-<candidate-id>.md`.

Preserve older controls. Copy the exact qualified bytes and compare their size
and SHA-256 with the tested source. Do not rebuild after qualification and
deliver different bytes with the earlier result. Distinguish boot media from
write-test input and post-test output; a deliberately disk-full or fault-damaged
fixture is not the user's normal boot image.

The boot README and final response must identify the absolute paths, sizes,
full SHA-256 values, source/component revisions, kernel/FreeCOM/VAEG identities,
actual tested model/configuration, ordinary launch command, required local ROM
configuration without bundling ROMs, drive assignments, and user steps for
safe disposable-media tests. Separate normal boot commands from diagnostics.

List passed and remaining acceptance rows, actual read/write and exchange
results, fresh-boot persistence results, memory configurations tested,
commit/CI identifiers, and automation/manual/hardware distinctions. Include a
precise supported media-exchange procedure and known detection limits.

## 13. Progress, consultation, and justified interruption

Maintain persistent progress after each meaningful experiment or repair:
current candidate, known-good control, last correct/first unresolved boundary,
hypothesis, next distinguishing action, tested image identity, acceptance rows,
and reproducible commands. Resume from it rather than asking the user to
reconstruct the session.

Report normally during work and save/present a checkpoint every 30 minutes of
active work. Include elapsed time, newly resolved uncertainty or validated
repair, current blocker, next action, completed/remaining rows, and the latest
tested candidate. Mark pending builds/CI as pending. A checkpoint does not
pause the task, create a background timer, or promise automatic resumption after
the execution environment ends.

Prepare/update private `M14-consult-current.md` when:

- 60 minutes of active investigation yields no new discriminating evidence or
  runtime-validated repair for the current blocker;
- two evidence-supported repair attempts leave the same failure unexplained;
- the next proposal changes architecture, accepted safety/compatibility scope,
  memory ownership, or a mandatory acceptance condition;
- source, emitted instructions, and runtime observations remain contradictory.

Additional trace volume or rebuilding unchanged code is not new progress.
Known build/CI waits are pending work, not proof of technical stagnation.
Consult earlier when the decision is already precise enough to state.

The consultation must contain one exact question, last good/first wrong boundary,
expected contract, relevant evidence, attempted repairs and excluded hypotheses,
remaining alternatives/tradeoffs, recommended next action, candidate identities,
reproducible commands, and useful independent work. Preserve prior consultations
before replacing the current file. Give the user the persistent path and a short
permitted summary; do not send private material to another service or claim
another reviewer was consulted unless that occurred.

Continue independent authorized work while waiting. Do not stack speculative
repairs on the disputed path. If new evidence resolves the decision within the
accepted design, record it, notify the user, and continue without renewed
permission. Do not ask the same unchanged question at every checkpoint.

Do not end merely because a run, capture, build, or hypothesis failed. Recover
and continue. An ordinary partial result is a progress record, not a routine
final handoff.

A final blocked handoff is justified only when an indispensable external input,
access, denied necessary action with no safe alternative, hard execution limit,
or unresolved prerequisite prevents further useful authorized work. A design
decision may justify `M14 DECISION NEEDED` after independent work is exhausted.
Persist exact restart state, question, alternatives, recommendation, and next
command. Do not relabel an ordinary unresolved code defect as an access failure.

## 14. Definition of done

Report `M14 PASS (VAEG)` only when the applicable mandatory acceptance rows pass
with the actual common kernel and VA FreeCOM, normal floppy writes persist,
media/error handling meets the recorded contract, required regressions and CI
pass, records agree, intended topic branches are pushed, and the exact tested
normal D88 plus reproducible disposable fixtures are delivered locally.

State hardware validation separately. Compile success, one raw sector write,
a host-side FAT modification, a diagnostic-only run, or a single file appearing
in DIR is not M14 completion.

Finish at M14. Record downstream implications for M15 and later storage work
without starting those milestones or moving MO earlier in the roadmap.
