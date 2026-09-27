# M16 goal: floppy formats, physical B: and native console input

Revision: 2026-09-27, retaining the 2026-09-25 floppy/input scope and adding
the owner-authorized measured-RAM and consecutive low-kernel layout contract.

Repository placement: `docs/tasks/M16-floppy-formats-console-input-goal-Codex.md`
inside the actual active parent worktree.

```text
/goal Read docs/tasks/M16-floppy-formats-console-input-goal-Codex.md in full and complete the new M16. Preserve the actual M15 baseline and existing work. Real VA hardware supports 2D according to the user, while the current VAEG does not: implement VAEG 2D support as mandatory M16 work in an isolated VAEG worktree, then qualify the guest against that exact build. Implement and qualify read/write support for 2D 320 KiB, 2D 360 KiB, 2DD 640 KiB, 2DD 720 KiB and the documented 2HC profile, physical FDD2 as B:, VA cursor behavior, VA and VA2 key auto-repeat, and native function keys through the common kernel and NECPC88VA FreeCOM. Resolve geometry and input contracts from actual sources before changing them. Renumber the former M16-M30 to M17-M31 exactly once, preserving historical evidence. Continue through required fixes, normal-launch acceptance, records, scoped topic commits/pushes, CI and exact tested-media delivery. Report every 30 minutes and consult on defined stagnation or broad design changes. Keep SCSI external, SCSI boot excluded and MO last. Do not start M17 implementation or claim untested support.
```

## 0. Objective, authority and new numbering

The user has inserted this implementation milestone at M16. The former M16
storage-contract/media-format task becomes M17; every former M17-M30 task moves
to M18-M31 respectively. M13-M15 retain their identities. This instruction
supersedes prior instructions that deferred these particular floppy/input items.

The user has supplied a concrete starting fact: real PC-88VA hardware supports
2D media, but the current VAEG implementation does not. Treat this as a known
emulator implementation gap and required M16 work, not an optional investigation
or an unsupported-hardware exemption. Record this premise as user-provided;
source inspection and bounded reproduction must locate the missing behavior,
not demand that the user re-establish the task's scope. Do not claim that this
prompt itself constitutes a new hardware test or a completed source audit.

Required scope:

- Implement VAEG support for the requested 2D 320/360 KiB profiles, including
  the actual image/drive/FDC path and its meaningful regression tests.
- Read/write data-volume support for 2D 320 KiB, 2D 360 KiB, 2DD 640 KiB,
  2DD 720 KiB, and 2HC after its exact profile is established.
- Physical floppy drive #2 as DOS B:, independently usable alongside A:.
- VA cursor-key input and correct native text-cursor position/visibility during
  console editing; preserve the corresponding working VA2 behavior.
- Key auto-repeat on both VA and VA2, with one responsible repeat producer.
- The actual VA/VA2 keyboard's function keys, delivered through the documented
  DOS/FreeCOM input contract with their supported shell behavior.

The user's corrected `VAVA2` wording means VA and VA2. Do not create another
machine type or implement only one model and claim both. The cursor request is
handled as console cursor keys plus the visible text cursor; it does not request
a mouse pointer, graphics cursor system or a general terminal emulator.

The user authorizes evidence-supported kernel/platform/FreeCOM changes, fixture
and harness work, required regression repairs, mandatory isolated VAEG 2D
implementation and other demonstrated scoped emulator fixes, acceptance records,
task-owned commits, normal topic pushes and applicable
CI. No renewed approval is needed for these routine steps. Preserve unrelated
work, private inputs, licenses and previously accepted repairs. Do not reset a
dirty checkout, force-push, merge a shared main branch or publish private data.

The owner explicitly added RAM measurement, effective boot-layout diagnostics,
LOADSEG semantics and consecutive low kernel/work placement on 2026-09-27.
These are scoped VA integration corrections and have the M16-MEMORY gate below.
They do not revive unrelated historical boot-progress proposals. Existing valid
implementations remain preserved. HDD/FAT16 runtime, SASI/SCSI
drivers, HDD boot, MO, NLS/Japanese conversion, LFN, FAT32 and a new memory manager
belong to later work. Guest low-level FORMAT support and bootability of every new
floppy format are not implied by data-volume read/write support.

## 1. Preserve the baseline and migrate the plan safely

Discover the actual active parent worktree, its component worktrees, branches,
dirty changes, source-of-record repositories, toolchain and build/CI commands.
Read applicable AGENTS.md files and current M13-M15 contracts, acceptance
reports, memory records and handoff. A historical
prompt or milestone label is not evidence of actual PASS.

Retain an immutable identified M15 control: sources/gitlinks, kernel, complete
packaged VA COMMAND.COM, loader/map, executable/configuration, model/ROM selection,
boot D88, ordinary launch and accepted input/disk results. Preserve recoverable
snapshots of task-owned dirty work before changing it. Reuse valid evidence and
run focused prerequisite checks; do not reopen the entire port after each edit.

Also discover the actual VAEG source repository, selected executable's source
revision, build configuration and applicable AGENTS.md/tests/CI. Prepare an isolated
VAEG topic worktree without repurposing the user's checkout. Retain the original
emulator binary/configuration and pair it with the M15 control. Keep VAEG and
FreeDOS source/build identities distinct; a guest commit alone does not identify
this milestone's working system. No renewed approval is needed for this scoped
VAEG implementation.

Apply the numbering map once to current plans, routing, active task filenames,
future status entries, links and handoffs. Use the supplied M13-M31 roadmap and
`M17-storage-contracts-media-formats-goal-Codex.md`. Retire the old active
`M16-storage-contracts-media-formats-goal-Codex.md` entry with an explicit redirect
or supersession record. The older `M16-floppy-console-followup-goal-Codex.md`, if
present, is task history and does not override this exact new scope.

Do not mechanically rewrite historical run IDs, report contents, commits, artifact
hashes or completed status. Record old-to-new identity and preserve links to
existing evidence. An earlier storage-contract result does not make new M16 PASS.
Do not discard work already started for the now-renumbered M17.

Use [the current M16 memory contract](../porting/m16-memory-layout.md), the
matched component sources and AGENTS.md. Historical memory notes remain
provenance; their saved-selection sizing and fixed staging/INIT addresses do not
override the active contract. Preserve M15 as an immutable control rather than
assigning its capacity results to a changed M16 binary.

Measure RAM with restored byte probes; do not derive capacity from backup RAM,
assume 640 KiB, reclaim unknown ownership, or add IBM INT 12h/15h sizing shims.
LOADSEG specifies the low resident base. Kernel work must follow it consecutively,
with paragraph alignment and owned MCB metadata only. Temporary staging and INIT
follow measured RAM top and are released after their last uses. Verify effective
numeric diagnostics, all relocations, low work/free boundaries and release.
Exercise the retained-setting failure configuration, non-default LOADSEG via
CONFIG.SYS, affected models, COM/MZ and guest write/readback on the exact candidate.
Report individual low-memory workload failures; host placement is not guest PASS.
Measure added resident data/code, transfer buffers, key queues and stacks against
currently qualified configurations. This correction does not authorize a new DOS
memory manager or changes solely to match MS-DOS behavior.

All source code, comments, diagnostics, technical reports and committed
documentation must be English. User-facing progress may be Japanese.

## 2. Resolve concrete media and input contracts

Read available local MD/TXT technical sources, especially the VA FDC/BIOS and
keyboard documentation where relevant. Use targeted `rg` searches and source
inspection. Missing original PDFs do not invalidate usable text sources. Record
evidence locators and distinguish
DOCUMENTED, SOURCE_FACT, RUNTIME_OBSERVATION, INFERENCE and UNKNOWN.

Inspect the actual kernel block driver, BIOS/native disk services, VAEG FDC,
drive configuration and image backend. Inspect both VA and VA2 keyboard paths,
matrix/native key translation, status/peek/read/flush ownership, timer behavior,
cursor routines and FreeCOM's enabled editing/function-key paths. Compare IBMPC
and NEC98 implementations only to understand contracts; do not transplant their
BIOS interrupts, ports, memory assumptions or scan codes without VA evidence.

### 2.1. Required floppy profiles

The four numeric capacities below are KiB payload targets, not D88 file sizes.
Container headers and track records are separate from guest-addressable bytes.

| Requested profile | Required data capacity | Required qualification |
| --- | --- | --- |
| 2D 320 | 327,680 bytes | FAT12 reads/writes on A: and physical B: |
| 2D 360 | 368,640 bytes | FAT12 reads/writes on A: and physical B: |
| 2DD 640 | 655,360 bytes | FAT12 reads/writes on A: and physical B: |
| 2DD 720 | 737,280 bytes | FAT12 reads/writes on A: and physical B: |
| 2HC | Determine exact profile from the local VA/FDC/media contract | FAT12 reads/writes on A: and physical B:; no silent substitution |

For every profile, establish cylinders, heads, sectors per track, sector length,
sector-ID range/order, encoding/data rate, drive mode and any required stepping,
BPB fields, FAT/root/data layout, usable payload length and supported container.
Check the geometry product against the requested capacity. Capacity alone is not
a sufficient format detector. Validate BPB and observed sector structure together.

Treat `2HC` as an explicit requested format name. Resolve its local meaning and
record exact capacity/geometry/density instead of silently changing it to 2HD,
reusing the existing native boot image, or assuming an IBM geometry from memory.
Keep the existing qualified native format as a separate regression profile when
it differs. A profile is mandatory; inability to implement it requires an honest
partial/blocked result and a concrete cause, not removal from the matrix.

For 40-track media in the configured drive, derive any step translation from the
actual drive/controller path. Do not assume that all drives require the same
stepping or that drive speed/density is determined by the FAT BPB. Guest code must
discover media through its real hardware/service interface, not by opening the
host D88 file or receiving a test harness's expected geometry.

Record supported data use separately from firmware boot and guest system-transfer
support. Preserve the accepted boot path. Do not mark a new format bootable merely
because DOS can read it after boot from a different format.

### 2.2. Input and cursor contract

Create a model-specific table covering ordinary characters, modifiers, cursor and
editing keys, every actual function key, and supported modified function keys.
Record the physical/matrix event, native translation, DOS character/extended-key
representation, repeat eligibility, release behavior and intended consumer.
Do not invent F11/F12, IBM scan codes or new shell shortcuts for absent keys.

Record the source owner and current validity of cursor position, visibility,
wrapping/scrolling, line editing and echo. Define the key-repeat delay/period,
time unit and timer owner using the existing native settings/API where available.
If no setting exists, choose documented constants appropriate to the existing
clock contract and explain them; do not add an unrelated settings UI.

Unknown details should trigger the next discriminating source/runtime check.
Continue independent work while resolving them. Consult only when available
evidence cannot determine an essential contract or the remedy needs a broad
architectural change.

## 3. Implement VAEG support and the guest floppy path

### 3.1. Mandatory VAEG 2D implementation

First establish a bounded failing 2D case using an independently inspected,
original synthetic 320/360 KiB fixture. Locate the missing stage in image loading,
format classification, drive configuration, physical-track mapping, FDC command
execution or writeback. Do not assume the gap is only a filename/enum check or
only the FreeDOS BPB. Keep the working native-format control available throughout.

Extend the production VAEG path to model the evidenced real drive/FDC behavior.
Inspect and implement the relevant parts of:

- The accepted D88/raw or other actual image backend's track/sector layout,
  record count/sector size and media identity; preserve container metadata and
  reject truncated/malformed layouts instead of guessing a writable default.
- Drive selection, physical-cylinder versus recorded track identity, any required
  stepping translation, head selection, density/rate/mode and sector-ID lookup.
  Derive translation from VA/controller evidence; never use a blanket factor of
  two or host-file padding to conceal an incorrect track mapping.
- Seek/recalibration, read/write command progression, result/status and relevant
  IRQ/DMA/timing behavior, including end-of-track/last-sector and not-ready/error
  handling in the existing controller model.
- Sector writeback, write protection, media insertion/removal, per-drive state,
  changed-format recognition and two simultaneously mounted different formats.

Do not replace the emulated controller with a FreeDOS-specific shortcut, modify
ROMs, special-case the test label/expected bytes, or convert 2D into padded 2DD
media just to make the existing backend accept it. Native 2D semantics must be
observable through the ordinary guest interface. Extend only the evidenced
missing stages; this is not authorization to rewrite the whole FDC.

Add focused synthetic tests that fail before the repair and pass afterward for
both requested 2D profiles. Exercise distinguishing first/last and track/head
boundary sectors, seeks, changed bytes after write/reopen, protection/errors and
independent drive selection. Use the production image/drive/FDC path at the
relevant boundary; a geometry helper test alone is insufficient. Keep public
VAEG tests ROM-free and use original fixtures.

Check relevant existing 2DD and native high-density cases for regressions; assess
2HC against the actual selected profile. Do not infer support for all formats
from the success of one 2D image. Run required VAEG tests/CI for the changed code,
then record the exact new executable and configuration for guest qualification.

### 3.2. FreeDOS integration and joint qualification

Use the qualified VAEG candidate to develop and test the actual FreeDOS disk
path. The dependency is VAEG 2D controller/media support -> guest block/FAT12
support -> normal FreeCOM workload and persistence. Independent B:/cursor/key
work may proceed while the emulator component is being repaired; this does not
make dependent 2D acceptance complete.

If both sides fail, isolate the controller boundary and guest contract with a
small distinguishing test. A guest workaround must not encode an emulator bug,
and an emulator repair must not manufacture a successful DOS result. Keep
emulator-only tests and actual guest acceptance as separate required evidence.


Extend the existing production block driver and media recognition. Keep common
kernel FAT12 file operations in use. Never substitute host-side file copying,
canned output, memory injection or special successful service returns.

Handle per-drive geometry/BPB changes, capacity bounds, transfer splitting across
sectors/tracks/heads, actual segment and transfer-buffer constraints, first/last
sectors, zero/invalid count semantics and relevant partial transfers. Derive DMA
limits from the VA path rather than importing IBM wiring assumptions.

Preserve protection state, truthful completed counts, bounded timeout/retry and
recovery. No write outside the selected unit/volume; reject malformed or unsupported
media before treating it as a writable default profile. Do not silently repair
or reformat input images. Keep geometry and cache invalidation synchronized when
switching between supported formats in the same drive.

Generate original controlled FAT12 fixtures using existing host tooling. Include
known small files, subdirectories, cluster/track-boundary files and sentinels near
the usable end. Inspect layouts independently. Test sector-level writes on separate
disposable raw fixtures, then file-level operations through the actual DOS kernel.
Never use destructive tests on the retained control or user media.

## 4. Implement physical FDD2 as B:

Map the actual second drive to its own DOS block unit/BPB/DPB and B: identity.
A reserved B: slot or a prompt to swap a disk in FDD1 is not physical B: support.
Both drives must be simultaneously mounted and distinguishable by controlled
labels and file contents. Do not implement B: by aliasing A:'s buffers/state.

Verify drive selection, head/seek operations, motor ownership, controller shared
state and completion routing. Keep media identity, cached geometry and changed-
media state separate per drive. Distinguish a shared-controller lock from unit
state; a command completing for one unit must not be credited to the other.

Support `B:`, `DIR B:`, `TYPE B:\<fixture>` and the contracted writable shell
operations, including actual `COPY A:\<fixture> B:\` and the reverse direction.
Preserve current/default drive semantics and return to a usable prompt.

Test different formats mounted at the same time, selection alternation, absent or
empty FDD2, write protection and media replacement in B: while A: remains mounted.
Ensure a B: error or swap does not change A:'s identity or send an old queued write
to a replacement disk. A physically absent drive must fail truthfully without a
hang or phantom successful I/O.

## 5. Implement VA cursor behavior

Follow cursor-key events through the native keyboard path into DOS and FreeCOM.
Repair the demonstrated producer/consumer mismatch so supported left/right/up/down
and editing behavior uses the intended native/extended-key representation. Do
not assume each cursor key must print a character or require a new history system
if the current shell does not implement that action.

Keep logical and visible text-cursor positions consistent after typing, supported
movement, insertion/deletion, backspace, Enter, line wrapping and scrolling. Use the
VA-native display/cursor mechanism. Respect the existing cursor visibility/blink
ownership; do not emulate IBM INT 10h or draw a second unrelated caret.

Verify the reported VA issue specifically and preserve VA2's working path. Capture
readable screen evidence where needed, plus state/consumer evidence to distinguish
a missing key event from a display-position defect. A diagnostic counter alone
does not prove visible cursor behavior. If physical GUI observation is unavailable,
state exactly which automated/display evidence was obtained.

## 6. Implement VA and VA2 key auto-repeat

Use exactly one repeat producer for each model. Determine whether the existing
native keyboard/firmware path already repeats before adding driver-level repeat.
Guest-visible repeat must work in the normal production launch with host frontend
repeat events disabled or otherwise excluded from double counting. Do not make
host SDL typematic or an automation interposer the required guest behavior.

Base repeat timing on the accepted guest timer/clock, not host sleep duration,
poll count, CPU speed or trace volume. Handle tick wrap, delayed polls and bounded
catch-up without unbounded bursts. Keep initial press, held state, repeat schedule
and release distinct; preserve correct active-low matrix detection if applicable.

Required behavior:

- A short press emits one logical key event.
- A held repeat-eligible key emits one initial event, waits the selected delay,
  and then repeats at the selected rate.
- Release cancels scheduled repeats; already queued events follow the documented
  queue contract, with no new repeat generated for the released key.
- A subsequent press rearms normally. Document behavior for multiple held keys
  and modifier changes; modifiers alone do not generate text.
- Repeated status/peek calls do not consume input, advance the repeat schedule
  multiple times or create extra events. Reads consume each queued event once.
- Flush/reset, queue-full and focus-loss/release handling follow one stated
  ownership policy; there must be no stuck repeat after focus loss or reset.
- Extended keys remain complete logical events; a full queue must not leave a
  prefix without its second byte. Do not erase held-key state just to manufacture
  another press edge.

Test ordinary characters, backspace and supported cursor keys on VA and VA2.
Specify which control/function keys repeat; do not silently repeat Enter, break
or destructive shell actions simply because all matrix bits share one loop.
Check a normal paced session and a faster emulation setting using guest time.

## 7. Implement native function-key delivery

Support all physical function keys in the selected VA/VA2 keyboard contract and
the modifier combinations actually specified. Preserve distinctions among keys
and among normal, shifted and other supported variants. Do not silently drop
unrecognized keys or convert them to arbitrary ASCII text.

Use the actual DOS console and FreeCOM extended-key convention. Where it uses a
prefix followed by a second byte, availability/peek/read must preserve the pair
and distinguish a valid zero prefix from no input. Verify this through the real
public DOS input path with a small original COM probe, not guest-memory injection.
Record code values and behavior from the selected contract, not IBM assumptions.

Exercise FreeCOM's enabled function-key editing/history features using the keys
documented by its actual source. If a physical key has no bound FreeCOM action,
show correct delivery in the probe and document that shell limitation. Do not
claim a shell feature from a probe alone, or require an invented binding for every
key. Preserve ordinary typing, control keys, flush and the status/read semantics
established during M13.

## 8. Required acceptance matrix

Maintain one matrix indexed by candidate, model, physical drive and media profile.
For the five requested profiles, both A: and physical B: are required. Exercise
each profile/drive pair on VA and VA2 using model-appropriate documented drive
configurations. A documented unavailable hardware combination must be identified
with its cause and workable supported configuration; never silently omit a
requested profile or relabel an unrun combination PASS. The currently missing
VAEG 2D support is a required implementation gap, not one of these physical
configuration limitations. It cannot justify skipping either 2D row, declaring
2D unsupported, or reporting a FreeDOS-only M16 PASS.

| Gate | Required evidence |
| --- | --- |
| M16-PLAN | New M16 and old M16-M30 -> M17-M31 migration applied exactly once to active records, preserving history |
| M16-BASE | Identified M15 control, current sources/build/configuration and native memory/ABI baseline |
| M16-MEMORY | Measured RAM independent of retained settings; actual LOADSEG path; consecutive resident/work/free boundaries; coherent temporary INIT fixups and release; exact-candidate layout, diagnostics, COM/MZ and file readback checks per the current memory contract |
| M16-VAEG-2D | Production VAEG 2D 320/360 support, discriminating synthetic controller/media tests, writeback and existing-format regressions; exact source/executable identity and applicable VAEG CI |
| M16-FORMATS | Exact 2D 320/360, 2DD 640/720 and 2HC profiles with independent layout validation and real guest reads/writes |
| M16-B-DRIVE | Physical FDD2 is B:, independent concurrent media, bidirectional cross-drive copy and correct drive selection |
| M16-MEDIA | Same-drive format changes, absent/not-ready/protected media, bounded errors, correct invalidation and non-target preservation |
| M16-PERSIST | DOS-created/changed/deleted files and FAT/directory state match expectations after close/flush and fresh VAEG reopen |
| M16-CURSOR | VA cursor-key delivery and native visible/logical cursor coherence; VA2 regression remains correct |
| M16-REPEAT | VA and VA2 short press, hold, delay/rate, release/repress, modifiers, queue/peek/flush and no double producer |
| M16-FKEYS | Actual physical function-key set and supported variants delivered correctly; probe and real FreeCOM evidence distinguished |
| M16-NORMAL | Production launch works without state patches/private interposers; actual common kernel and packaged VA FreeCOM are used |
| M16-REGRESS | Required M13-M15 behavior, memory bounds, affected components and required public CI pass |
| M16-HANDOFF | FreeDOS and VAEG source/executable/configuration pairing, status/manifests/commits/CI agree; exact tested boot/data images, launch instructions and new M17 handoff delivered |

Use controlled guest sequences including edited input, DIR/TYPE, COPY/REN/DEL/MD/RD
where contracted, cursor movement/repeat/function-key actions, COM/MZ execution,
prompt return and another successful command. Choose mixed-format cross-drive
cases that expose wrong unit and stale geometry; the full Cartesian product of
every source/destination format is unnecessary unless a concrete risk requires it.

Verify writes persist by closing the relevant guest files, performing the defined
flush/clean-stop sequence and reopening the exact resulting image in a fresh VAEG
process. Host-side inspection validates actual guest-produced bytes; it must not
repair them before validation. Track intended mutable images separately from
pristine controls, and distinguish backing-file protection from emulated media
write protection.

Synthetic key events through the normal frontend are valid automated evidence if
they exercise the real guest matrix/firmware/driver path. Label them automated.
Do not claim physical typing or hardware PASS unless those tests occurred. Retain
per-model evidence rather than treating a VA2 success as proof of VA behavior.

## 9. Emulator delivery, privacy and publication

The VAEG 2D work in section 3.1 is mandatory. Other demonstrated scoped VAEG
FDC/drive/keyboard/display defects may also be repaired in the isolated task
worktree. Each change needs an expected contract and a discriminating preferably
ROM-free test. Keep diagnostics separate from behavior changes, requalify affected
guest cases with the actual selected executable, and run required VAEG regressions
and CI. Do not patch firmware, hard-code private ROM addresses or make the emulator
recognize this test's expected output.

Keep private documents, ROMs, proprietary images, derived values, traces and
disassembly under the existing excluded evidence policy. Public code/tests/CI use
permitted public or original synthetic inputs. Preserve root GPL-2.0-or-later and
component licenses. Do not publish private evidence as a side effect of a test.

After actual local acceptance, review scoped diffs/privacy, commit and push child
topic branches before parent gitlinks, update locks/records, commit and push the
parent topic, and run applicable CI. Fix actual failures and verify CI belongs to
the final relevant revision. Do not reuse an older green run for changed behavior,
weaken gates or refresh unexplained goldens. Include the VAEG topic commit/push
and applicable CI; record the selected executable's full SHA-256, build settings
and source revision in the FreeDOS acceptance manifest. Update an existing pin or
lock according to repository conventions; do not invent a VAEG submodule if it
is a separate repository. No shared-main merge is authorized.

## 10. Durable artifact delivery

Use the Git-excluded `.private-evidence/m16-floppy-input/handoff/` directory in
the active parent worktree.
Keep it distinct from historical storage-contract evidence formerly called m16.
Do not delete or move old evidence merely to make directory names match the plan.

Deliver the exact tested normal boot image and the controlled data images for all
five profiles, with uniquely named pristine and post-test roles. Include full
SHA-256, byte size, profile and payload capacity, drive assignment, source/build
and emulator identities, per-model results, ordinary launch instructions and the
command/key sequences. A D88 file's byte size is not its floppy payload capacity.
Copy tested bytes and compare hashes; do not deliver an untested rebuild.

The handoff requires the matched VAEG build as well as the tested disk images.
Give its absolute executable path, size/full SHA-256, source commit and any dirty
state, build command/toolchain/configuration, normal launch command, required
model/drive/media options and applicable CI result. Preserve the control build.
Do not tell the user to run the newly accepted 2D images with the old unsupported
VAEG binary. If the emulator is rebuilt, distinguish the new artifact and run the
necessary affected qualification before attaching acceptance to it.

Include a short user boot README and detailed manifest/handoff. If a diagnostic
image differs, give it a separate identity and qualification. Do not bundle ROMs.
The final response must provide absolute image paths, full hashes, exact launch
procedure, tested formats/models/drives, remaining limitations, and commit/CI
identities. Provide the next task as M17 storage contracts, preserving external
SCSI in M20/M21, SASI boot in M19 and MO in M30/M31.

## 11. Persistence, checkpoints and consultation

Update a persistent private progress record after every meaningful decision,
experiment or validated fix: candidate/source identity, last correct and first
incorrect boundary, evidence, hypothesis, next discriminating action, remaining
matrix rows and current tested artifacts. Keep runs finite in time/output and
check exit statuses. Fix failed harness triggers and continue; do not reuse stale
results or generate repeated giant traces without resolving a new uncertainty.

Save and present a concise checkpoint every 30 minutes of active work, with normal
updates more frequently. Reporting does not stop the task or promise background
execution after the session ends. Pending build/CI results remain pending.

Prepare private `M16-consult-current.md` when 60 minutes yield no discriminating
evidence or validated repair, two evidence-supported repairs leave the same
failure unexplained, evidence contradicts the model, or the next step requires a
broad architecture/ABI redesign. Include one precise question, last good/first
bad boundary, source and runtime evidence, attempts, alternatives, recommendation,
candidate identities, reproduction commands and independent work that can continue.
Notify the user; do not claim an outside reviewer was consulted unless that occurred.

Continue independent authorized work while awaiting advice. Do not stack speculative
repairs on the disputed path. If evidence resolves it within the accepted scope,
record the resolution and continue without renewed approval. Do not repeatedly ask
the same unchanged question or turn the consultation trigger into a trial quota.

## 12. Completion and legitimate interruption

Report M16 PASS only when the required scope and acceptance matrix, relevant
VAEG 2D implementation, joint emulator/guest regressions, both repositories'
records and topic pushes/CI, and exact matched executable/media handoff are complete.
Do not end routinely at a diagnostic discovery, one repaired key, one floppy format
or an intermediate PARTIAL. Complete the next necessary authorized action.

If an indispensable input/access or an unavoidable execution limit is unavailable,
finish independent work, preserve a precise restart point and report the concrete
blocker. If all remaining work depends on an unresolved design decision, use
`M16 DECISION NEEDED` with a recommendation and alternatives. A documented physical
constraint is not evidence of supported operation; report it without weakening the
requested gate. Never claim PASS by omitting VAEG 2D implementation, either 2D
profile, 2HC, B:, VA, VA2 or the required keys.

Finish this M16 and hand off to M17. Do not begin the later storage implementation
merely because its former milestone number was M16.
