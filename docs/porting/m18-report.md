# M18 work report

Status: **IN PROGRESS — source-build gates pass at the current public tip;
required guest and memory-qualification gates remain incomplete.** No M18 PASS,
release designation, archive, or HANDOFF READY is claimed.

Evidence labels: **HOST PASS** for the source-build checkpoint at
`d55b17afbe8d63ffc69eaaea03b6fa97c5a6e21e` only; this is not full M18
acceptance. **VAEG PASS: NOT ESTABLISHED**; targeted guest workflows pass, but
required qualification is incomplete. **DEFERRED HARDWARE VALIDATION**; hardware
is NOT RUN.

`START_SHA`: `d81bba18f0e4793d7165fb0acfdf7e229e160c83`.
`QUALIFIED_IMPLEMENTATION_SHA` is not established. The publication tip and
downstream base belong in a separate post-push handoff; this report cannot
contain its own future commit identity.

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
allocation policy retains a 32-cluster working-space estimate, not a measured
guest EDLIN/JWASMR workflow peak. Tool RAM minima and practical largest-block
requirements remain unmeasured.

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

The source review of `PreConfig2()` and `P_0()` found no demonstrated stale
memory ownership defect. No kernel memory code was changed. A matched
physical/resident/MCB ownership table, full DOS allocation/EXEC accounting,
stable repeated-child memory evidence, low-memory tool behavior, and actual
per-tool RAM minima remain unrun. The hypothesis that conventional memory is
unusable due to stale reservations is unresolved; absent MCB entries are not
being treated as free memory. The source ownership ledger, release-barrier audit
and runtime-observer caveat are in [m18-memory-audit.md](m18-memory-audit.md).

## Maintenance adapter correction (qualification pending)

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
synthetically. Real guest qualification of this additional probe is pending.
The dedicated CI now composes the separate QA media after the complete normal
two-build gate. Neither QA implementation nor the scoped allocator results close
the remaining full memory-ownership and per-tool acceptance gates.

## Remaining qualification and scope

The following required guest gates remain **NOT RUN or incomplete**: JWASMR
peak/largest-block measurement and broader low-memory stress; full shell/file regressions with A:
and physical B: media, including exchange during operations; complete FORMAT/SYS
safeguard coverage beyond the targeted tests above; observed working-space
peak; memory ownership and capacity accounting. Any test not yet executed is
not a pass. No hardware test was attempted. Initial capacity scripts did not complete their
full workloads and remain unqualified. Later matched-executable capacity runs
completed the bounded workload described above; they do not establish all-tool
minima or a near-limit allocation/EXEC stress pass.

The disk payload is the FreeDOS kernel, NECPC88VA FreeCOM, COUNTRY.SYS, EDLIN,
MORE, MEMMAP, real-mode JWASMR, CHKDSK, FORMAT and SYS, plus English/ASCII
starter material and license notices. Maintenance tools are limited to native
2HD FAT12 media: CHKDSK is read-only; FORMAT writes filesystem metadata only
to a prepared B: volume with a valid native 2HD BPB; SYS transfers the selected
M18 A: system files to a prepared 2HD B: target. No SASI/SCSI runtime, HDD boot,
FAT16 guest access or hardware support is claimed. FreeDOS version reporting
remains unchanged.

Before designation, rebuild the corrected committed source twice from clean
public exports, verify equality and current exact-tip CI, then finish all
applicable guest, memory, media and maintenance qualification on the exact
candidate. Keep M18 partial and do not archive a distribution image or begin
M19 until the required gates are complete. Hardware may remain `NOT RUN`.
