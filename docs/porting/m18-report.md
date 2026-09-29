# M18 work report

Status: **IN PROGRESS — source-build gates pass at the current public tip;
required guest and memory-qualification gates remain incomplete.** No M18 PASS,
release designation, archive, or HANDOFF READY is claimed.

Evidence labels: **HOST PASS** for the source-build checkpoint at
`04854df8bccfc62abb61fd861f0381b539f9703e` only; this is not full M18
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
candidate, not designated or archived. The current source delta contains a quickstart/test correction for EDLIN
command case. It has not yet been built into a new candidate or covered by CI.

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

The uppercase EDLIN `E` command wrote the file but did not leave the editor.
Inspection of the pinned public EDLIN source identifies a case-sensitive exit
flag after case-insensitive command dispatch. No component source was changed;
the starter quickstart and its host regression now explicitly use lowercase
`e`. The correction requires the normal source rebuild and exact-tip CI before
publication.

The source review of `PreConfig2()` and `P_0()` found no demonstrated stale
memory ownership defect. No kernel memory code was changed. A matched
physical/resident/MCB ownership table, full DOS allocation/EXEC accounting,
stable repeated-child memory evidence, low-memory tool behavior, and actual
per-tool RAM minima remain unrun. The hypothesis that conventional memory is
unusable due to stale reservations is unresolved; absent MCB entries are not
being treated as free memory.

## Maintenance adapter correction (qualification pending)

Source review of the pinned kernel's `entry.asm:int2526` established that DOS
returns result CF live and leaves the original caller FLAGS word on the stack.
The M18 maintenance adapter incorrectly tested that original word, masking I/O
errors. The adapter now discards it with POP and tests live CF. A production
8086 adapter test independently models read/write returns with opposite original
and result carry values, verifies error propagation (including zero-error-code
fallback), far-call arguments, preserved registers and stack balance. All six
cases failed before the correction; the complete 57-test host suite passes after
it. No kernel/component code was changed. Full source builds, exact-tip CI and
guest maintenance qualification for this correction are still pending.

## Remaining qualification and scope

The following required guest gates remain **NOT RUN or incomplete**: JWASMR
low-memory behavior and measured minimum; the complete fresh-boot starter
workflow on the rebuilt corrected candidate; shell/file regressions with A:
and physical B: media; read-only CHKDSK; FORMAT and SYS safeguards and
successful boot transfer on disposable native media; observed working-space
peak; memory ownership and capacity accounting. Any test not yet executed is
not a pass. No hardware test was attempted.

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
