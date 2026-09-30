# M18 work report

Status: **M18 PASS for the refreshed, single designated native 2HD disk.**
`HANDOFF READY` is separate and requires post-push checks of the publication
tip and its own CI; this committed report cannot record its own future SHA.

The host-side outputs now use the requested names
`dist/m18/freedos-PC88VA-M18-2HD.D88` and
`dist/m18/freedos-PC88VA-M18-SOURCES.tar.xz`. Producer, manifests, acceptance
verifier and instructions use the same names; the old names are rejected by
the new verifier. The rebuilt D88 and designated compressed archive are
**byte-identical** to the HELLO.DOC-qualified disk. No new guest or hardware
run is claimed by this host-only filename change. The guest evidence remains
bound to that exact disk built and tested at
`203983964a5892f8c79c365151f0703b573ba931`; the source companion changes to
include the maintained filename recipe and its provenance.

Evidence labels: **HOST PASS** at qualified implementation
`99a8f59a0ec7388cc16968a8814aa23bb0ba8c92`: 94 host tests, two clean
source-build containers per run, two independent identical complete local
distributions (all eight generated files), separate allocator QA media, the
M18-local instance/dependency verifier, and successful native x64 exact-head
CI `36690434903` attempt 1 with identical D88/source-bundle SHA-256 values.
**VAEG PASS** for the bounded VA/VA2 workflows on the *refreshed* normal D88
SHA-256 `ace43378a504b1af5bad3d6e89184c1e193d6abf85c995b7a94b581a7d743e5c`
with matched executable SHA-256
`c13cba54f95ae4b575495dd85194a43948bf59713ad1dede0d717dc072482dbf`.
**DEFERRED HARDWARE VALIDATION**; hardware is NOT RUN. Failed or unrun earlier
checks remain historical and are not retroactively promoted to PASS.

`START_SHA`: `d81bba18f0e4793d7165fb0acfdf7e229e160c83`.
`QUALIFIED_IMPLEMENTATION_SHA`: `99a8f59a0ec7388cc16968a8814aa23bb0ba8c92`.
`PUBLICATION_TIP_SHA` and `DOWNSTREAM_BASE_SHA` belong in the separate
post-push handoff, not in a self-referential committed report.

## Refreshed HELLO instructions and current designated image

The owner requested build instructions **inside** `HELLO.ASM` and a separate
plain-ASCII `HELLO.DOC` with an explanation and actual build steps. Both
files are on the disk; `README.TXT` and `QUICKSTR.TXT` point to the guide.
The supported command is `JWASMR -0 -bin -Fo=HELLO.COM HELLO.ASM`, followed by
`HELLO.COM` **only after successful assembly**; it needs no linker. The
existing fail-closed `BUILD.BAT` also builds/runs the MZ example. This edit
changed only on-disk source/instructions/package/media composition, not any
DOS binary, loader, CONFIG.SYS or component gitlink. Independent FAT inspection
found the only changed existing files to be `HELLO.ASM`, `README.TXT` and
`QUICKSTR.TXT`, plus newly added `HELLO.DOC`; every executable is byte-identical
to the earlier distribution. The first M18 distribution at source 679 and its
D88 SHA-256 `991370d0...dd12` remain historical evidence, **not** guest
qualification for the different current D88 bytes.

The **only current designated** archive is
[the M18 native 2HD D88 xz archive](../../images/milestones/m18/README.md),
303,000 bytes, SHA-256
`e399db6aa1775e3b61f76f1b6e9bb7abcb80de35271f1b0d34ff75dc7d18d5dc`.
Its extracted 1,331,888-byte D88 has the exact guest-qualified SHA-256
`ace43378a504b1af5bad3d6e89184c1e193d6abf85c995b7a94b581a7d743e5c`.
Two independent XZ Utils 5.2.5 locked-container compressions were identical;
extraction was compared byte-for-byte with the new D88. Its host-side
corresponding-source/license companion is **not** a second floppy or committed
build product: `freedos-PC88VA-M18-SOURCES.tar.xz`, 2,225,716 bytes, SHA-256
`6283512d3002c67a7b118fecdbb373cb7789d62e03bcf62abb9fbcddbd3470d4`,
recreated from the public qualified source and pinned dependencies. The FAT12
native 2HD image has 20 distribution files, 650 allocated and 619 free
1,024-byte data clusters. The complete guest edit/assemble/repeat workflow
(including its DOC/source readback and output files) stayed within the
committed 32-cluster reserve and 128-free-cluster floor at its settled
checkpoint. Individual in-process peaks are **NOT MEASURED**.

Both VA and VA2 at **640 KiB installed** read back the original `HELLO.DOC`
and pre-edit `HELLO.ASM` byte-for-byte, saved an EDLIN edit with an intact
backup, assembled and executed COM and relocated MZ examples, rejected invalid
and missing assembler inputs without stale executables, and checked matched
post-warmup/post-repeat DOS MCB ownership. At **512 KiB installed** with a
stale retained 640-KiB selection, both edited/saved/reopened a source and
safely rejected COM and MZ JWASMR DOS EXEC without outputs; source-generated
native B: FORMAT, read-only CHKDSK and SYS passed on both, and both exact
SYS-produced B: disks separately booted and wrote/read guest files. SYS-only
media lack MEMMAP, so no SYS-disk MCB PASS is claimed. With this same new
normal D88, both models also passed header-protected A: byte preservation,
live B: exchange and separate **nonbooting 2D-D88** B: copy/write/readback;
these fixtures are not designated distributions. A fresh normal-disk VA2
input regression and VA2 no-numeric-coprocessor REAL4 assembly/execution
also passed. No physical keyboard or all-linked-opcode proof is inferred.
CHKDSK A: redirection remains issue #12, **not** an A: check PASS. EDLIN
editing at 256 KiB and sample assembly at 512 KiB remain non-passes; 640 KiB
is an installed-RAM setting for the tested *small* example, not a promise for
arbitrarily large source files. Useful in-program RAM and instantaneous disk
workspace peak remain **NOT MEASURED** by owner decision. Ownership remains
bounded by the DOS MCB chain; no firmware/VRAM interval was reclassified free.

The sections below preserve earlier source/guest checkpoints, including the
first qualified disk. Their numeric file counts, image/archive identities and
qualifications bind to their stated **historical** source/D88, not this
refreshed distribution.

## Baseline and provenance

M18 starts from integrated `main` merge `d81bba18f0e4793d7165fb0acfdf7e229e160c83`,
with parents `1af9974700cd4dd1164cc0df56cc062925376148` and
`06b0536feae627e9935277376b16630cb735fb24`. M16/M17 accepted behavior and
records were not rewritten.

The locked component inputs are fdkernel
`e87e8071c355a99a7f34a8758d4a3368b6523f3d`, FreeCOM
`29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`, COUNTRY.SYS
`23f189cca3420606eae8723884fa92ccd65eb307`, EDLIN
`c036c43adbdaa5693bb4cd3f4f3c65090f1c9d57`, and JWasm
`96d1f3d4c1661c85788297d50ab032e452f48978`. JWasm is a public fork commit
parented by upstream v2.20 `ac54827ff40b77ecd6e77ed0866a43fc60cd5fe1`; its
source and license notices are included. No component source was vendored into
the parent and no upstream branch was pushed.

## Host source-build evidence

At public parent tip `04854df8bccfc62abb61fd861f0381b539f9703e`, the M18-local
`make m18-disk` recipe exported committed allowlisted inputs and exact component
gitlinks, then completed two clean network-disabled Linux/amd64 builds. The
builds produced identical D88 bytes and release records. They checked linked
placement, native 2HD geometry/BPB/FAT12 data, payload hashes, cluster chains,
package records and exact image readback. Exact-tip native x64 CI run
`36463965573` succeeded, including the M18-local host suite, public-source
audit, and complete two-build comparison. The 56-test local suite also passed.
The pinned toolchain image is
`sha256:3c465999ab43719da8209eb19d273b4c8208f4544ba75b9063cf4b5b494d0c17`;
the pinned Unicorn 2.1.4 host-test wheel SHA-256 is
`9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239`.

The exact built candidate at that tip is
`dist/m18-memmap-bounded/PC88VA-M18-2HD.D88`, 1,331,888 bytes, SHA-256
`ab3ea20baea41fc375248516356bd3f1e0d9efe9f3bb87e6c2c2f7e94410d6ce`;
its source bundle SHA-256 is
`2ce8d3f7148a41bcd841c95bde48752c2ced8a454d1856f3d1711530d61be690`. It is a
historical candidate, not designated or archived.

The EDLIN guide correction was committed as
`6260f44fcdde5b7608f86bab35bcf90710e1dc5c`, clean-built twice, pushed and tested
successfully by exact-tip M18 CI run `36513756503`. The historical M03 census
rejected the additional M18 component set; commit
`808d00d0e486c49c0fd76195d5c145b2578362b6` routes this topic to its complete
M18 source-build gate instead of the frozen three-component M03 census.

The latest behavioral checkpoint is
`d55b17afbe8d63ffc69eaaea03b6fa97c5a6e21e`. All 57 local host tests and two
independent network-disabled source builds passed; the topic is pushed and
component pins are unchanged. Its exact-tip M18 CI run `36514810539` succeeded,
including the complete isolated two-build gate and clean-source check. The candidate is
`dist/m18-media-binding/PC88VA-M18-2HD.D88`, 1,331,888 bytes, SHA-256
`8cf309a78b9346dc22594ac2e115fbb26d9744953ff4c8bdde5f3246357751de`.
Its companion `PC88VA-M18-SOURCES.tar.xz` is 2,194,228 bytes, SHA-256
`226486e29bb5c0565fd10d6a8a03b752a3433f79210faa3346359385ed06ad7b`.
Neither is designated or archived.

The subsequent report-only tip
`19f73f4cba301143af2c1d66895b6c6dc749f1f9` also clean-built identical disk bytes
locally, but CI run `36516412091` failed fetching optional command-not-found
metadata from the Ubuntu snapshot (HTTP 502), before tests or compilation.
The workflow now disables that irrelevant metadata and translations and bounds
APT retries while retaining the exact NASM package/version check. Qualification
of this CI correction is pending; the failure is not counted as a pass.

The accepted native 2HD profile is 80 cylinders, two heads, eight
1024-byte sectors per track, FAT12, and 192 root entries. The M18 host
allocation policy retains a 32-cluster working-space reserve. Later exact-disk
settled copy/edit/build readback qualified that reserve; it does not measure an
instantaneous peak. Source-derived MZ EXEC lower bounds and native-capacity
functional tests are separate; not every practical workload limit is qualified.

## Guest and memory evidence

The exact candidate passed the previously failing `MEMMAP /CHECK` guest test in
the scoped no-backup-memory run; redirected MEMMAP output was read back by DOS
`TYPE` and `DIR`, and the guest-written D88/FAT contents were independently
inspected. This is targeted VAEG evidence, not full guest qualification.

A subsequent targeted starter workflow copied the original COM/MZ examples to
A:, edited and saved the COM source with EDLIN using lowercase `e`, observed the
prior file as `HELLO.BAK`, and read the edited and backup files. JWASMR produced
a COM and an MZ executable; both were run separately and displayed their
expected sample messages before returning to the shell. Before/after MEMMAP
snapshots were redirected and independently read from the guest-written disk;
each reported a valid MCB chain. MORE `/?` help and page advancement were
also exercised, with control returning to the shell. JWASMR help, a syntax
error, and a missing-source error returned control; the syntax-error test
started with previously generated executables, and the guest D88 readback
confirmed BUILD.BAT removed them without creating a replacement COM. MEMMAP
`/CHECK` still reported a valid chain. The VAEG tests used the source-built
candidate and an empty B: drive. These results do not establish low-memory
behavior or a measured RAM minimum.

The fresh ordinary VA starter workflow was repeated on the exact latest
maintenance-corrected candidate, with B: empty. EDLIN's backup and edited source,
guest-generated COM/MZ files and valid before/after MEMMAP snapshots were read
back independently. Both programs displayed their expected messages and returned
to the shell for another successful memory check. VA2 boot was separately
compared with the exact M17 control using M17's accepted emulator executable;
both reached FreeCOM. The full starter workflow was then repeated on VA and VA2
with the exact accepted executable, B: empty, and fresh candidate copies.
Independent FAT inspection verified edited/backup source, guest COM/MZ output,
redirected messages from both executed programs, valid MCB checks and matching
before/after memory accounting. The fixed small JWASMR samples succeeded in the
tested 640-KiB configuration; fresh 256/384/512-KiB runs rejected both assembly
attempts without producing executables, returned to the shell, and preserved
matching before/after MCB accounting. This establishes these bounded workload
results, not arbitrary-source fit or all-tool minimum requirements. Guest
records distinguish the locally rebuilt emulator executable from the earlier
accepted executable; a shared source revision alone is not executable identity.

The uppercase EDLIN `E` command wrote the file but did not leave the editor.
Inspection of the pinned public EDLIN source identifies a case-sensitive exit
flag after case-insensitive command dispatch. No component source was changed;
the starter quickstart and its host regression now explicitly use lowercase
`e`. The correction has completed the normal source rebuild and exact-tip CI.

At this **earlier checkpoint**, source review of `PreConfig2()` and `P_0()`
found no demonstrated stale ownership defect; the then-unrun allocator,
repeated-child and low-memory checks were subsequently performed within the
owner-scoped gates below. No kernel memory code was changed, and absent MCB
entries are not treated as free physical memory. The lifetime ledger,
release-barrier audit, qualified boundaries and remaining unknowns are in
[m18-memory-audit.md](m18-memory-audit.md).

## Maintenance adapter correction (historical checkpoint; later qualified)

Source review of the pinned kernel's `entry.asm:int2526` established that DOS
returns result CF live and leaves the original caller FLAGS word on the stack.
The M18 maintenance adapter incorrectly tested that original word, masking I/O
errors. The adapter now discards it with POP and tests live CF. A production
8086 adapter test independently models read/write returns with opposite original
and result carry values, verifies error propagation (including zero-error-code
fallback), far-call arguments, preserved registers and stack balance. All six
cases failed before the correction; the complete 57-test host suite passes after
it. No kernel/component code was changed. Both this correction and the binding
correction below completed full two-build source checks and were pushed.

A second integration defect was isolated to initial removable-media binding.
The pinned VA `media_check_io()` deliberately rejects unbound/changed media
rather than silently redirecting an existing absolute-sector operation. Tools
must establish their binding before starting work. The maintenance volume opener
and FORMAT now call DOS AH=32h once at operation entry, reject its error result,
and never rebind or retry inside absolute-sector I/O. Host fixtures cover failed
initial binding with no reads/writes and mid-operation invalidation with no
rebind. This preserves the kernel's existing media-generation protection rather
than relaxing it.

On the exact latest candidate, automated normal guest input exercised FORMAT's
A: rejection and B: cancellation, successful metadata initialization on disposable
B:, read-only CHKDSK, SYS transfer, and a subsequent valid MEMMAP check. Independent
M18 FAT readback compared all five transferred files with the source disk and
verified source A: remained unchanged. A separate fresh boot of the actual
SYS-created target reached FreeCOM and wrote/read back a file; host readback
confirmed its bytes. Write-protected source/target copies booted and supported
read-only checks; FORMAT failed and returned to a usable shell, with both disk
hashes unchanged. These scoped results do not replace the remaining media-change,
capacity, alternate-model and memory qualification gates.

## Kernel date reproducibility correction

A later clean build exposed a wall-clock-dependent `__DATE__` in the linked
kernel's display string. Comparing the retained linked image and the new image
isolated the difference to that date; matching same-day builds had not proved
cross-date reproducibility. Earlier image identities remain historical results,
not final release qualification. The build now supplies the pinned component's
existing `KERNEL_BUILD_DATE` interface from the committed epoch, with an explicit
compiler wrapper preserving all other arguments. The linked-banner checker
rejects missing, duplicate or drifted dates. This is declared non-semantic build
metadata, not a linked-binary patch or a component source change. The changed
kernel identity requires clean carrier/placement verification and fresh guest
qualification before any acceptance claim.

At `cf5ea87f1c06dfb254bd5d31ae6dffca3af5e56b`, all 62 local host tests and two
complete clean builds passed, including carrier/placement and linked-date checks.
Dedicated native CI run `36544910571`, attempt 1, passed at that exact head.
The separately composed allocator QA media also matched across two compositions.
Fresh automated VA/VA2 guest runs of the new normal bytes completed the A:-only
EDLIN edit/backup/save, JWASMR COM/MZ build, execution and independent file
readback sequence, with valid matching before/after MCB summaries. These are
scoped results, not full M18 acceptance.

The new QA producer also explicitly selects NASM as the compiler-container
entrypoint rather than passing its executable to the image's Bash entrypoint.
A failed initial QA build was retained and is not a guest result.

## Allocator QA implementation

An original 8086 allocation probe and a separate `make m18-allocator-qa` producer
now cover own-block shrinking, DOS 48h/49h/4Ah allocation/free/resize, occupied
neighbor rejection, coalescing, owner preservation, zero-payload blocks, invalid
handles within probe-owned payload, exact-largest allocation and recovered
capacity across 16 rounds. The QA target first clean-builds the complete public
normal disk, then verifies source/archive/payload bindings before composing a
separate QA disk. It never reads an old D88 template. The probe is not included
on the normal disk. Synthetic tests reject stale QA inputs and check that initial
shrink failure produces a failure exit rather than a PASS marker. The original allocator probe then passed under the actual pinned DOS kernel
on VA and VA2 at the lowest/highest configured capacities, with unchanged valid
before/after MCB reports. Both models also passed with installed RAM reduced
while retaining an unmodified larger-capacity backup-memory selection from a
preceding guest session. The retained selection was checked separately before
and after; no setup session or backup edit was used to make detection succeed.
Precise runtime measurements and identities remain in private evidence.

A further separate QA EXEC probe now implements exhaustion rejection, measured
COM/MZ boundary overhead and 32 repeated pairs while preserving guard ownership
and capacity. Its initial-shrink failure path and child relocation are tested
synthetically. Initial guest runs of this additional probe did not complete and are not PASS.
Source review found a QA fixture defect: the 16-byte COM's live code overlapped
`load_transfer`'s 24-byte initial register frame at the bare minimum allocation.
The fixture now owns explicit trailing stack space. A new host regression models
that pre-entry write and rejects the old fixture. The expected COM boundary is
31 tail paragraphs, including environment, split MCB, PSP, image and stack;
the MZ boundary remains 83 under the pinned FreeDOS page-rounding policy.
Bounded progress output was added to the QA parent. Later real-DOS validation of the corrected probe passed as recorded in the
source-bound guest checks below; no common-kernel change was made.
The dedicated CI now composes the separate QA media after the complete normal
two-build gate. Neither QA implementation nor the scoped allocator results close
the remaining full memory-ownership and per-tool acceptance gates.

## Runtime observer trimming (historical checkpoint; later qualified)

The next MEMMAP implementation replaces the incomplete initial-MZ-only policy
with the pinned Watcom runtime's documented `_nheapshrink`/`_fheapshrink` calls.
After stdout is primed, only unused heap tails are returned; active stack, data,
stdio storage and environments remain owned. Failure is a nonzero exit before
MCB traversal. No kernel reservation, foreign owner or guessed linked minimum
is resized. A synthetic integration test checks ordering and both failure
returns. Build records now separate linked requirements, FreeDOS whole-page
initial allocation and actual runtime ownership; they no longer claim the
linked minimum is the complete process footprint. That implementation checkpoint ran 67 host tests; later clean builds, exact
candidate guest comparisons and an expanded host suite supersede this pending
gate as recorded below.

## Later source-bound guest checks (M18 remains in progress)

At behavioral checkpoint `b772f72fc6c2fb5ba548b567e10cc21374ef8307`,
the full double clean build and exact-head native M18 CI run `36552873414`
passed. The ordinary disk has been freshly booted on matched VA and VA2.
Each guest edited and saved a source copy, assembled and executed both sample
formats, handled assembler syntax and missing-input failures without accepting
stale outputs, and ran repeated COM/MZ children. The post-warmup MEMMAP files
are byte-identical. The earlier before/after text differs only in the shell's
unreliable descriptive name bytes; all non-name MCB fields and totals match.
A printed name is not evidence of a changed allocation. Neither result proves
that the observer can see physical regions outside the DOS arena.

On separate VA/VA2 and stale-selection QA disks from the same build, the
allocator and bounded COM/MZ EXEC probes passed, with valid identical
before/after MEMMAP reports. A matched 256/640-KiB control compares the old
observer and the new Watcom API trim: independent filesystem readback and
MCB arithmetic reconcile the freed tail exactly to the observer's own
runtime allocations and headers; unchanged other owners are not reclaimed.
Numeric observations and guest images are retained only in Git-excluded
private evidence.

A separately invoked `tools/m18/qa/workspace_readback.py` now validates
completed guest copy/edit/build snapshots against the precise public D88 and
manifest, including the unchanged boot sector and root, editor backup, real
COM/MZ outputs and the committed workspace reserve. The first attempted BUILD
checkpoint exited before BUILD was injected; it remains an incomplete run.
A new completed BUILD run visibly executed both examples and independently
passed stage readback. On the later exact normal disk, independent copy, edit
and build guest runs again reached their intended stages; the build visibly
executed both examples and returned to a valid MCB report. The same-source
readback checked the unchanged distribution files, editor backup, generated
COM/MZ programs and reserve. The inspector now rejects unaccounted WORK files
while allowing the explicitly optional observer output. Settled snapshots do
not directly measure instantaneous in-program disk or RAM high-water marks.
The owner removed both the in-program useful-memory and instantaneous disk-
workspace-peak measurement requirements from M18 acceptance. Retain source-
bounded intermediate file lifetimes, the conservative disk reserve, and staged
guest readback without claiming an unmeasured peak. The inspector writes private evidence
outside the public repository; neither guest disks nor numeric observations
are public build inputs.

The same exact normal bytes were booted separately on both models to run MORE
paging and help, followed by valid MEMMAP checks and another shell command.
Readback confirmed the distributed files were unchanged. For a protected A:
copy, failed writes did not change the D88 bytes or create a guest file. The
initial protection run lacked an answer to the DOS critical-error prompt and
is not a recovery PASS; subsequent runs explicitly chose Fail. The VA2 screen
showed recovery and an interactive shell. A separate shorter VA control then
showed recovery at a usable prompt; independent readback confirms the entire
protected image stayed unchanged in both cases. A milestone-local
public-input-only, nonbooting 2HD B: fixture producer now exists without an old
candidate disk. Both models used two independently prepared disposable B:
paths: after a live media swap, each disk retained only its own distinct guest
file; CHKDSK B: and the subsequent DOS MCB check passed. The VA2 screen showed
both reads and the prompt. The VA final screenshot was blank, so its results are
limited to independently read-back guest writes and checks, not a visual
console claim.

## Same-candidate maintenance and no-coprocessor check

The `1705f56ae1f829441a3fc56ef560d8e89fd8bc81` checkpoint preserves the
exact previously guest-tested normal D88 bytes, while publishing new
M18-local QA media preparation and workspace helpers in its independently
rebuilt source bundle. All local host tests and exact-head native M18 CI run
`36648740861`, attempt 1, succeeded; complete M18 qualification remains open.

Matched VA and VA2 separately booted the same normal A: disk with freshly
source-generated, disposable nonbooting B: media. Both ran FORMAT B:,
CHKDSK B: and SYS A: B:, with a valid subsequent memory chain. Independent
FAT readback found precisely the selected five SYS system files on B:, with
bytes equal to the current source disk. Each exact SYS-produced disk, before
any host-side file injection, was then booted with FDD2 empty and wrote/read a
new guest file. VA2 visibly returned to the prompt with its file contents and
directory shown. VA ended at a visible prompt; its written file was independently
read back, but the final display did not show the TYPE command. Neither run is
a hardware result or a claim that SYS copied unselected applications.

A separate VA2 guest used the matched normal disk with its optional numeric
coprocessor explicitly disabled. JWASMR assembled an original 8086 COM source
containing a real-number data initializer, produced and ran the result, and
returned to a valid DOS MCB chain. The output data encoding was independently
inspected. Pinned Watcom's linked map includes both its real-number conversion
routine and DOS software 8087 emulator. A new build verifier fails if a later
link omits the required emulator; the host negative tests do not substitute for
the guest result. On the later unchanged-byte normal disk, both VA and VA2
repeated the no-coprocessor REAL4 assembly and COM execution. Independent FAT
readback verified the generated program's floating initializer, success report
and subsequent valid DOS MCB chain. VA2 also showed the commands and check on
screen; VA's final screen showed only prompts, so its visible-console claim is
restricted to independent readback. Neither test proves hardware or every
floating operation. Further CPU/VA startup and library review remains required.

At smaller installed capacities, actual normal-disk sample-assembly requests
failed without leaving executable outputs and with stable checked MCB reports;
one case retained a larger backup-memory selection. This qualifies clean
failure on those tested cases, **not** a successful minimum for JWASMR or every
other utility. An earlier CHKDSK stdout redirection was empty and is not
accepted as a successful disk check. Separate same-image low-memory tests did
read a newly generated 2HD B: with CHKDSK and load/quit the original HELLO.ASM
in EDLIN at 384 KiB on VA and installed 512 KiB on VA2 with a stale larger
retained setting. For the later exact notice-updated candidate, VA at 384 KiB
also completed **destructive** FORMAT B:, read-only CHKDSK B: and SYS A: B:;
the B: system files match the A: source, and the actual SYS-produced disk
subsequently booted at 384 KiB and wrote/read a new guest file. The first
redirected CHKDSK A: output in that session was empty and is not counted as
a check; B: inspections did produce validated content. A later isolated
A:-target redirection again yielded an empty result file. This remains
[public issue #12](https://github.com/nakatamaho/freedos-pc88va/issues/12),
**not** a CHKDSK A: PASS. A screenshot is retained only in private evidence;
no ROM-dependent capture is attached to the issue. Its cause is undetermined,
and an unredirected A: check was NOT RUN.

A separate 384-KiB VA editor run saved a modified source copy, preserved the
byte-identical `.BAK`, reopened the file in EDLIN, independently read its
contents and returned to an identical, valid normal MEMMAP snapshot. Its last
redirected `/CHECK` file was empty because the run ended before that command
completed; **that invocation is not a `/CHECK` PASS**. These results do not
prove alternate-model low-memory destructive work.

At 256 KiB, a directed EDLIN load reported no source lines and ended
abnormally; CHKDSK, FORMAT and SYS rejected their operations for insufficient
DOS memory, with a usable shell and matching checked MCB snapshots afterward.
An independent **unredirected** EDLIN run on the later notice-updated normal
candidate visibly printed Watcom's `Out of memory` and `ABNORMAL TERMINATION`.
The subsequent typed TYPE command was partly consumed during termination and
its redirected output was empty, so it is **not** a file-read PASS. The original
source file remained byte-identical to the clean normal disk, a later shell
write/readback marker was present, and a subsequent MCB check passed. This is
a bounded explicit resource failure with shell recovery, **not** successful
EDLIN editing at 256 KiB. The pinned upstream EDLIN path reports zero lines
when it cannot open a file; do not repair that upstream behavior solely to
conceal low-memory pressure. The owner accepts 256 KiB as too little for EDLIN:
the supported editing floor is 384 KiB. This is **not** an EDLIN issue or an
authorization to shrink another owner's memory. Runtime useful-memory peaks
are not measured and are no longer a required M18 result.

The owner narrowed the outstanding functional capacity review to **installed
512 KiB**, not an exhaustive new per-tool RAM-minimum matrix. On the unchanged
normal disk with a stale larger retained selection, both VA and VA2 edited,
saved and reopened an EDLIN source copy with an intact backup; MORE help and
paging returned to a subsequent checked MEMMAP command. Independent FAT
readback confirmed unchanged distributed files and matching before/after MCB
reports. The first input fixture accidentally issued MORE twice and was
aborted; it is not counted. The corrected runs' late shell marker did not
complete, so that marker is also not a pass. These are scoped 512-KiB results,
not evidence that other models or settings passed unrun operations.

On separate source-generated native 2HD B: disks at installed 512 KiB in both
models, real FORMAT B:, CHKDSK B: and SYS A: B: completed. Independent D88
readback found only the selected, source-identical SYS files and source boot
sector on each B:, with valid source-A MCB checks. Both exact SYS-produced
disks then booted and wrote/read guest files. The SYS-only disk does **not**
contain MEMMAP: an attempted command printed a missing-command error and its
redirected check file was empty; no MCB check on that disk is claimed. On the
normal disk at installed 512 KiB, VA2 visibly reported a DOS EXEC allocation
failure for JWASMR COM/MZ. Independent VA and VA2 FAT readback found failure
markers, no new executables and valid checked shell/MCB chains; VA's final
screen alone did not show the commands. Previously qualified 640-KiB assembly is
a separate success, not a 512-KiB success. The owner accepted that the small
JWASMR assembly workflow cannot run at installed 512 KiB: the documented
sample setting is **640 KiB installed**, not a stale retained selection.
512-KiB boot, editor and native maintenance remain supported within their
observed scope. Neither speculative kernel reclamation nor a second tools disk
is warranted. This is not a guarantee for larger assembly sources.

An M18-local private readback inspector now reconciles the exact public
carrier/D88 identity with selected post-shell MEMMAP snapshots at every native
capacity, including a stale retained selection. Its checks account for the
resident/first-MCB boundary, kernel-work block, all PSP owners, end-exclusive
MCB links, headers, totals and measured installed RAM top. Symbolic
source-owned interval equations and distinct temporary lifetimes are in
`m18-memory-audit.md`. Neither MCB traversal nor linked-placement arithmetic
asserts unknown firmware/VRAM occupancy or an in-program maximum.

The matched VA and VA2 frontend input paths recalled the preceding FreeCOM
command with F3 and edited a typed filename using the cursor-left key; the
expected independent guest files and checked MCB chain were read back. A VA2
held-key run produced repeat characters through the guest's own input path,
recorded in a file; the first fixture accidentally omitted the ECHO separator
and left its target file empty, and is explicitly not counted for repeat.
Automated frontend input is not a physical keyboard or hardware result.

On the notice-updated normal disk, VA and VA2 separately edited and saved
the bundled sample, read it back, assembled and executed real COM and relocated MZ
programs, recovered from syntax and missing-input errors without stale
executables, and returned to a valid MCB chain. The initial pre/post snapshots
were not byte-identical; **post-warmup and post-repeated-child snapshots**
matched, and repeated COM/MZ output files were independently inspected. A
separate M18-local QA fixture preserves the accepted public 360-KiB FAT12 data
geometry on a nonbooting 2D-D88 B: disk, with the normal 2HD A: unchanged.
VA and VA2 read/wrote files to this mixed B: and the independent 2D-D88/raw
FAT readback agreed with guest A: readback and stable MCB snapshots. The
initial 360-KiB **raw .img** attempt failed because the matched emulator did
not recognize that container; it is preserved as a non-pass, not counted as
an adapter failure or silently renamed into the working 2D-D88 fixture.
M18 CHKDSK/FORMAT/SYS remain deliberately 2HD-only.
The official Open Watcom 1.9 source release was separately obtained and
hash-checked for the linked DOS software-8087 and floating-conversion modules
and its license. The host package manifest and on-disk/host instructions identify
that **public upstream source archive** separately from the pinned official
compiler binary and from the project/component corresponding-source bundle.
The compiler runtime is unmodified. Any change to on-disk notice text yields
a new normal D88 and must be guest-tested by its **new** exact identity before
release designation.

## Owner-scoped limits and historical open gates

The owner removed two requirements: establishing programs' useful memory
use during execution and an instantaneous disk-workspace peak. Both remain
**NOT MEASURED**, and neither the MZ EXEC lower bounds nor settled workspace
readbacks are relabeled as peaks. Keep the committed disk reserve, exact-disk
staged checks and live-ownership safety rules. Do not infer physical firmware
or VRAM ownership from the DOS MCB chain.

The owner-scoped 512-KiB workload review is complete for the listed tools and
safe JWASMR rejection, with 640 KiB **installed** required for the qualified
assembler samples. An earlier on-disk notice changed the normal D88 identity:
boots of preceding candidates could not qualify it. The final exact-byte
retests and clean build are recorded below. Empty redirected CHKDSK A: output
remains [public issue #12](https://github.com/nakatamaho/freedos-pc88va/issues/12)
and is **not** an A: check PASS or a reason to relabel independently read-back
B: checks. Any unrun test is not a pass; no hardware test was attempted. Initial
capacity scripts that did not finish remain unqualified; the owner does not
require an exhaustive minimum for every utility. Allocator/COM/MZ near-limit
EXEC stress used separate source-bound QA media, not the normal disk.

The disk payload is the FreeDOS kernel, NECPC88VA FreeCOM, COUNTRY.SYS, EDLIN,
MORE, MEMMAP, real-mode JWASMR, CHKDSK, FORMAT and SYS, plus English/ASCII
starter material and license notices. Maintenance tools are limited to native
2HD FAT12 media: CHKDSK is read-only; FORMAT writes filesystem metadata only
to a prepared B: volume with a valid native 2HD BPB; SYS transfers the selected
M18 A: system files to a prepared 2HD B: target. No SASI/SCSI runtime, HDD boot,
FAT16 guest access or hardware support is claimed. FreeDOS version reporting
remains unchanged.

## First qualified single-image publication (historical; superseded)

The qualified `679fb32dee9709ca298d70b5168bd0dbbd32d601` source and exact
five component gitlinks clean-built two independent complete local distributions
from fresh committed exports. **All eight generated public distribution files**
were byte-identical between those runs; each run independently built the complete
DOS disk twice in isolated, network-disabled Linux/amd64 containers. Native
exact-head CI `36674161070`, attempt 1, also passed the same 91-test host suite,
public privacy audit, two-build source pipeline, separate allocator QA producer
and shared `make m18-accept` instance/dependency verifier. Local and native CI
both produced the same normal D88, 1,331,888 bytes, SHA-256
`991370d0c075f75153192e94365c3c798c3ca50639aaeb716054ab6c5da4dd12`,
and corresponding-source/license bundle, 2,224,012 bytes, SHA-256
`afcac120b9fcab6a080187d74d06daa97b00f053421d604ea474e3eeac8d341d`.
BuildKit-local Docker config IDs differed across hosts; public toolchain records
instead use the exact committed toolchain-lock profile
`sha256:39c5b3052d71463235a26e8704ab54c1fedb51ee75bb4efb55e6229391a95162`,
while verifying local executable/compiler, Python, liblzma/xz and assembler
identities before use. Only nonsemantic parent Git TAR headers were canonically
rewritten in that pinned environment, with source bytes and executable modes
verified unchanged. Component Git archives were not rewritten. Earlier
cross-host bundle drift and the failed QA CI attempt `36672838956` remain
recorded as **failures**, not passes.

At the first M18 publication, the **then-only** designated image was stored
at `images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz`
([historical manifest](https://github.com/nakatamaho/freedos-pc88va/blob/d5ba0ebbd9fb8e50ac2c822f699379b48747c1e8/images/milestones/m18/manifest.json)),
302,316 bytes, SHA-256
`5d7ebb3dd0a29ec817b58c35a2c1550fdb39b810983eaf5c5c33ea24848c5f60`.
Independent pinned-container compressions were byte-identical; decompressing
that earlier archive reproduced its own exact guest-qualified D88. Its
historical public manifest binds uncompressed and compressed hashes/sizes,
exact source/gitlink/archive/toolchain identities,
license references and validation limits. The companion sources are generated
from the qualified public source commit, not committed as a second archive or
installed on another floppy. The normal FAT12 profile is 80 cylinders, two
heads, eight 1024-byte sectors per track: 19 distribution files, 648 allocated
and 621 free data clusters (635,904 free data bytes). The committed sample
workspace policy reserves 32 clusters and a 128-free-cluster floor; the
independent exact-disk settled copy/edit/build readback stayed within the
reserve. **Instantaneous** workspace peak and useful in-program memory remain
**NOT MEASURED** by owner decision.

The exact disk and matched executable booted on VA and VA2. With 640 KiB
**installed**, both edited/saved/reopened an EDLIN source, preserved its
backup, assembled and executed COM and relocated MZ starter programs, recovered
from assembler errors, ran repeated children, and returned to valid matched
post-warmup/post-repeat DOS MCB ownership; the no-coprocessor VA2 REAL4 sample
also assembled, executed and passed independent byte/MCB readback. At 512 KiB
installed **with a stale larger retained selection**, both edited/saved and
reopened an EDLIN source and safely rejected JWASMR sample EXEC without an
executable or lost shell. VA and VA2 each ran real native 2HD FORMAT B:,
CHKDSK B: and SYS A: B: on public-source-generated B: disks; both actual
SYS-produced disks then booted and wrote/read guest files. A separate
write-protected normal A:, live-exchanged native B: media, and nonbooting
360-KiB 2D-D88 B: controls passed independent media readback without adding
another distribution disk.
A fresh copy of the designated normal image also passed the automated VA2 F3,
cursor and repeat-input regression; two earlier faulty/nonfresh input fixtures
remain non-passes for the claims they did not establish. Protected-media and
VA2 display claims are limited to the separately read-back files and actual
visible output. CHKDSK A: redirected emptiness is **not** a filesystem-check
success, and the SYS-only disks have no MEMMAP for a checked-MCB claim.

Every shipped parent-built DOS C executable selects Watcom's 8086 `-0` DOS
model; the native raw-media assembly declares `cpu 8086`. Source and linked
startup review found DOS real-mode `_cstart_`, Watcom's linked software 8087
support for JWASMR, and an IBM INT16h keyboard call only in EDLIN's disabled
`SHIFT_JIS`-guarded path, not the English release. No exhaustive all-linked-
branch opcode proof or hardware result is inferred. The kernel/source ownership
review and matched DOS allocator/EXEC tests found no stale permanent kernel
reservation to reclaim; the guarded boot-time temporary release, firmware
exclusion policy and other live owners remain intact. An MCB chain is not a
physical firmware/VRAM map. The confirmed repairs are limited to M18 adapter
error FLAGS/media binding, deterministic banner metadata, and MEMMAP observer
heap trimming; none invent a new DOS implementation or shrink an unrelated
owner. Selected M18 source, package/CPU/VA attribution, Open Watcom runtime
source URL/hash and individual licenses are documented in the accompanying
source bundle, the image manifest and on-disk English notices.

Use `make m18-disk` after the documented pinned toolchain setup, then
`make m18-accept M18_DIST=dist/m18`; the exact qualified source checkout and
extraction commands are in the archive README. The current M13–M32 route is
unchanged. **M19 SASI-data work is not started**: its downstream handoff must
preserve the M17 storage contracts and this qualified memory/single-disk
baseline. Publication-tip CI, remote equality, ancestry and the bounded
report/archive-only diff are verified in the separate post-push handoff.
Hardware remains **NOT RUN / DEFERRED HARDWARE VALIDATION**.
