# M18 work report

Status: **IN PROGRESS — source-build gates partly passed; guest qualification is
blocked by a MEMMAP runtime failure and exact-tip CI has failed.** No M18 PASS
or HANDOFF READY is claimed.

Evidence labels: **HOST PASS: NOT ESTABLISHED** (the exact-tip native x64 CI
run failed); **VAEG PASS: NOT ESTABLISHED** (scoped guest execution found a
failure); **DEFERRED HARDWARE VALIDATION** (hardware is NOT RUN).

`START_SHA`: `d81bba18f0e4793d7165fb0acfdf7e229e160c83`. A `QUALIFIED_IMPLEMENTATION_SHA`
has not been established. The publication tip and downstream base belong in a
separate post-push handoff; this report cannot contain its own future commit
identity.

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

Before the guest finding, the M18-local `make m18-disk` recipe exported
committed allowlisted inputs and exact component gitlinks, then completed two
clean network-disabled Linux/amd64 builds. It checked linked placement,
native 2HD geometry/BPB/FAT12 data, payload hashes, cluster chains, package
records and exact image readback. Both builds matched. The pinned toolchain
image is
`sha256:3c465999ab43719da8209eb19d273b4c8208f4544ba75b9063cf4b5b494d0c17`;
the pinned Unicorn 2.1.4 host-test wheel SHA-256 is
`9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239`.

The exact tested pre-fix candidate was built from parent tip
`b8cccb9c42ce007a8d53695794f306ec02cbd159`. Its native 2HD D88 is 1,331,888
bytes with SHA-256
`ae198059b95d7d02943ea7f59480df392984f369d7d03a2fe99db815e222c32e`. This
candidate is not designated or archived. Host readback confirmed the configured
80-cylinder, two-head, eight-sector/track, 1024-byte-sector FAT12 profile and
valid file/FAT records. The sample-workflow disk-space policy is an estimate;
the actual EDLIN/JWASMR peak remains unmeasured.

The M18 host suite passed 53 tests locally and in the two clean build
containers for the pre-fix source. Exact-tip native x64 CI run
`36458214567` completed with **failure**: the runner did not have NASM although
the M18 host placement/media tests require it. The workflow is being corrected
to install the NASM version from the shared toolchain lock; no CI pass is
claimed until a new exact-tip run succeeds.

## Guest finding and memory investigation

A source-built, unmodified VAEG executable reached the DOS shell in a scoped
run of the exact pre-fix candidate; a guest file copy/readback was independently
checked. This is only a smoke test, not `VAEG PASS` or full guest qualification.

The same candidate's MEMMAP `/CHECK` operation caused DOS to report a corrupted
MCB chain and halt. This is a blocking application defect, not evidence of a
kernel ownership defect. A temporary diagnostic build isolated the failure to
MEMMAP's runtime AH=4Ah resize path; the read-only parser path did not reproduce
it. The proposed correction bounds MEMMAP's MZ maximum allocation at load time
and removes runtime resizing. The changed source passed 56 local host tests and
the public-source audit, but has not yet been clean-built in the isolated
containers or guest-tested. The failure is not considered fixed.
Private emulator configuration, numeric observations and raw captures remain
in Git-excluded evidence.

The source review of `PreConfig2()` and `P_0()` found no demonstrated stale
memory ownership defect. No kernel memory code was changed. A matched guest
physical/resident/MCB ownership table, full DOS allocation/EXEC accounting,
stable child-return evidence and measured per-tool RAM minima remain unrun. The
memory-waste hypothesis is unresolved; M18 has not established that
reservations are stale or that all remaining RAM is necessary.

EDLIN editing/save/reopen, MORE paging, JWASMR assembly and COM/MZ execution,
syntax/missing-input recovery, alternate floppy regressions, the complete
starter workflow, and CHKDSK/FORMAT/SYS destructive-operation safeguards on
disposable media remain **NOT RUN**. The guest workflow's disk-space peak is
also **NOT RUN**. No hardware test was attempted.

## Scope and next work

The disk payload is FreeDOS kernel, NECPC88VA FreeCOM, COUNTRY.SYS, EDLIN,
MORE, MEMMAP, real-mode JWASMR, CHKDSK, FORMAT and SYS, plus English/ASCII
starter material and license notices. Maintenance tools are limited to native
2HD FAT12 media: CHKDSK is read-only; FORMAT writes filesystem metadata only
to a prepared B: volume with a valid native 2HD BPB; SYS transfers the selected
M18 A: system files to a prepared 2HD B: target. No SASI/SCSI runtime, HDD boot,
FAT16 guest access or hardware support is claimed. FreeDOS version reporting
remains unchanged.

- Commit and push the MEMMAP MZ-allocation correction and the CI dependency
  correction. Run all host regressions and two complete clean builds from the
  exact public inputs, then verify the new exact-tip native CI run.
- Boot the changed candidate in the previously failing guest configuration and
  repeat MEMMAP `/CHECK`, map redirection and independent readback. Continue the
  required shell, utility, assembler, disk-space and disposable-media gates on
  the exact resulting D88. Preserve the failing candidate and evidence.
- Keep the report and handoff partial unless all required gates pass. Do not
  designate/archive an M18 image or begin M19 until the active milestone is
  buildable from its exact public revision and its required qualification is
  complete. Hardware may remain `NOT RUN`.
