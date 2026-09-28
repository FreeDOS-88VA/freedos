# M18 work report

Status: **IN PROGRESS — public source build verified locally; guest qualification
and exact-tip CI are not complete.** This is not `M18 PASS` or HANDOFF READY.

Evidence labels: a local double build and 53 host tests have passed, but no
`HOST PASS` is claimed before native x64 CI verifies the exact publication tip.
`VAEG` is **NOT RUN**. **DEFERRED HARDWARE VALIDATION (NOT RUN)**; hardware is
optional and no hardware result is claimed.

`START_SHA`: `d81bba18f0e4793d7165fb0acfdf7e229e160c83`.
`QUALIFIED_IMPLEMENTATION_SHA`: `2a4d9a29cf98a40941df0f6e769caa0dc6b8adcb`
(the source/build implementation passed local host tests and a clean double
build only; it is not guest-qualified). The final `PUBLICATION_TIP_SHA`,
`DOWNSTREAM_BASE_SHA` and exact-tip CI bindings belong in the separate post-push
handoff; this report cannot contain its own future commit identity.

## Baseline and provenance

M18 starts from the selected integrated `main` merge `d81bba18f0e4793d7165fb0acfdf7e229e160c83`,
with parents `1af9974700cd4dd1164cc0df56cc062925376148` and
`06b0536feae627e9935277376b16630cb735fb24`. The topic branch descends from
that exact commit. M16/M17 accepted behavior and records were not rewritten.

The locked component inputs are fdkernel
`e87e8071c355a99a7f34a8758d4a3368b6523f3d`, FreeCOM
`29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`, COUNTRY.SYS
`23f189cca3420606eae8723884fa92ccd65eb307`, EDLIN
`c036c43adbdaa5693bb4cd3f4f3c65090f1c9d57`, and JWasm
`96d1f3d4c1661c85788297d50ab032e452f48978`. JWasm is a public fork commit
parented by upstream v2.20 `ac54827ff40b77ecd6e77ed0866a43fc60cd5fe1`; its
corresponding source and license notices are included. No component source was
vendored into the parent and no upstream branch was pushed.

## Local host build and package work

The M18-local `make m18-disk` recipe exports committed allowlisted M18 inputs
and the exact component gitlinks, verifies their public provenance, then uses
network-disabled Linux/amd64 containers to build twice from clean exports. It
checks linked placement, native 2HD geometry/BPB/FAT12 data, per-file hashes,
cluster chains, package records, and exact image readback. Both clean builds
matched. The pinned toolchain image is
`sha256:3c465999ab43719da8209eb19d273b4c8208f4544ba75b9063cf4b5b494d0c17`;
the pinned Unicorn 2.1.4 host-test wheel SHA-256 is
`9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239`.

The host-built candidate is one native PC-88VA 2HD D88 (80 cylinders, two
heads, eight 1024-byte sectors per track; 1280 logical sectors; FAT12). Its
size is 1,331,888 bytes and SHA-256 is
`ae198059b95d7d02943ea7f59480df392984f369d7d03a2fe99db815e222c32e`. Host
readback found 646 allocated and 623 free data clusters, with 20 of 192 root
entries used. The configured sample-workflow policy is 32 clusters, leaving
591 after that estimate. The actual EDLIN/JWASMR guest peak has **not** been
measured; the build explicitly reports it pending and this policy is not guest
qualification.

A host-side corresponding source/license bundle accompanies the D88 and
contains the allowlisted parent build inputs and source archives for all pinned
components. Its exact size and SHA-256, along with the parent revision, are
recorded in the generated build manifest. The local distribution contains a
package manifest, capacity record and two-build comparison. These are generated
local candidates, not yet a designated or archived milestone release.

The same 53 M18 host tests passed in `make m18-host-tests` and in the clean
build containers. The build also runs the M18 isolation and public-source
checks. A first complete build caught a DOS interrupt-vector symbol-decoration
mismatch in the maintenance disk-I/O adapter; it was corrected and the
subsequent full double build passed. No failure was bypassed with an old image
or saved DOS executable.

The disk payload is FreeDOS kernel, NECPC88VA FreeCOM, COUNTRY.SYS, EDLIN,
MORE, MEMMAP, real-mode JWASMR, CHKDSK, FORMAT and SYS, plus English/ASCII
starter material and on-disk notices. Maintenance tools are limited to the
native 2HD FAT12 profile: CHKDSK is read-only; FORMAT only initializes filesystem
metadata on a prepared B: volume with a readable valid native 2HD BPB; SYS
transfers the selected M18 A: system files to a prepared 2HD B: target. No
SASI/SCSI runtime, HDD boot, FAT16 guest access, or hardware support is claimed.
FreeDOS version reporting remains unchanged.

## Memory investigation and unrun acceptance

The source review of `PreConfig2()` and `P_0()` found no demonstrated stale
memory ownership defect. No kernel memory code was changed. There is not yet a
matched guest physical/resident/MCB ownership table, a before/after allocation
account, an INT 21h allocation/free/resize and COM/MZ EXEC test, stable
child-return evidence, or a measured per-tool RAM minimum. The memory-waste
hypothesis is therefore unresolved; M18 has not established that reservations
are stale or that all remaining RAM is necessary.

MEMMAP has a bounded host-tested synthetic MCB parser and is built for the
pinned FreeDOS AH=52h/layout interface. DOS self-resizing, ordinary output,
`/?`, `/CHECK`, redirection and independent guest comparison are **NOT RUN**.
EDLIN editing/save/reopen, MORE console paging, JWASMR assembly/COM/MZ execution,
syntax/missing-input recovery and low-memory behavior are **NOT RUN**.
CHKDSK/FORMAT/SYS destructive-operation safeguards have host source/media tests
but no disposable guest-media or SYS-result boot test. The starter workflow's
peak disk-space use is **NOT RUN**.

No usable PC-88VA guest emulator is currently available for this work. VAEG was
not modified. Native VA/VA2 boot, normal prompt and shell operations, A:/B:
regressions, read-only/write-protected boot, guest memory comparison and all
runtime utility gates remain unrun. No hardware test was attempted.

## Next work and closure conditions

- Add and run the native x64 workflow against the exact pushed source tip; publish
  its complete build and host-test result with a separate post-push handoff.
- Preserve the generated candidate and arrange an unmodified usable PC-88VA
  guest environment. Run the required matched memory, normal boot, utility,
  assembler, disk-space and disposable maintenance-media qualification against
  the exact D88 bytes; do not infer a pass from host construction.
- Do not change kernel ownership code without runtime evidence. Do not designate
  or archive an M18 distribution until every required guest/memory/public-build
  gate is resolved. Hardware may remain `NOT RUN`.
- M19+ remains pending. If M18 cannot proceed without an unavailable guest
  environment, record the precise blocker and leave this milestone partial; do
  not relabel it PASS or begin the SASI data milestone.
