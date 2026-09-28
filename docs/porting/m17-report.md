# M17 work report

Status: **IN PROGRESS; not M17 PASS and not HANDOFF READY.** The accepted M16
baseline remains PASS / HANDOFF READY. M17 does not claim HDD runtime, guest
SASI/SCSI support, or hardware success.

START_SHA: `f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4`. The required M16
predecessor CI runs 36381203803 and 36381203807 both succeeded at that exact
head. Accepted fdkernel source: `7883c8fac11fab20cb467ad0a93c8799f35b565a`;
FreeCOM: `29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`; COUNTRY.SYS:
`23f189cca3420606eae8723884fa92ccd65eb307`.

## Provenance in progress

- Parent integration base: `0852dc543ca9c23829a8059776e2f77072ceb947`, with
  original M17 work parent `6ef9a327d58e712e8470b5e6746c850c54852bcd` and
  accepted M16 parent `f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4`.
- fdkernel M17/M16 merge: `e87e8071c355a99a7f34a8758d4a3368b6523f3d`, with
  parents `1527da489528367bb8028a8e9576375d35722f50` and
  `7883c8fac11fab20cb467ad0a93c8799f35b565a`. Its deterministic source-archive
  SHA-256 is
  `887857e0c6706e47a9c8ea2055f74b3891138ed00564585a0053795e9e7dbc69`.
  The merge was pushed to the `nakatamaho` origin branch and the exact remote
  tip was verified. No push was made to upstream.
- The parent M17 implementation, build verifier, and documentation remain
  unpublished. The M17 lock retains `START_SHA` and the exact M16 predecessor
  CI bindings.

## Implemented and locally tested

- Preserved common FreeDOS CONFIG.SYS/FDCONFIG.SYS behavior and the bounded VA
  CONFIG/INIT integration. No operational external HDD driver was added.
- Added strict schema-v2 storage profiles, checked unit/range conversions,
  deterministic synthetic FAT12/FAT16 fixtures, explicit nonbootable and
  unqualified status, and an independent read-only inspector.
- Added five separate CONFIG/FDCONFIG QA image profiles and synthetic
  character-device, zero-unit, state, and memory probes. These are test inputs,
  not guest boot or storage-driver qualification.
- Added fail-closed acceptance metadata and output checks for exact component
  provenance, predecessor CI claims, clean source archives, pinned toolchain
  and wheels, two-build artifact identity, D88 payload composition, M16 floppy
  regressions, M17 storage fixture readback, and schema/instance validation.
  Negative tests cover stale CI bindings, unknown/missing fields, malformed
  hashes, path escape, extra/missing/tampered artifacts, and build-log drift.
- Verified the pinned Linux/amd64 Open Watcom image:
  `sha256:51a0b466cdc32377f3d2bec8e6e5432428fce13813723de3ce185eac989698df`.
- Focused host tests: storage **19 passed**; CONFIG QA **4 passed**; acceptance
  verifier **7 passed**; component remote safety **2 passed**. The full host
  discovery run executed 76 tests: **67 passed; 9 errored only because the
  host lacks the pinned Unicorn dependency**. This host run is not acceptance.
- The public VAEG `Main_RAM_Auto` MinGW static build was completed separately
  from an isolated checkout. Its artifact and import audit are recorded in the
  VAEG build report; Windows execution and emulator interaction were not run.

## Required verification still pending

Not yet run against a committed exact M17 parent candidate:

- Complete allowlisted source export and two independent offline builds,
  artifact-manifest comparison, and the linked carrier/placement regression
  gate. The new end-to-end acceptance verifier has only had its focused unit
  tests run; it has not yet checked full build outputs.
- Full M17 tests in the pinned Linux/amd64 environment with the identity-pinned
  Unicorn wheel, including actual CONFIG QA image and synthetic media
  validation.
- Guest boot of the exact candidate, including default CONFIG, FDCONFIG
  precedence, character INIT, zero-unit INIT, and non-default LOADSEG. The
  required VAEG ROM/firmware environment has not been identified; no guest
  CONFIG/DEVICE result is claimed.
- Parent publication, exact-tip public CI, final source/handoff bindings, and
  final privacy review. No M17 distribution archive is designated.

The storage fixtures do not establish SASI discovery, SCSI I/O, guest FAT16,
HDD boot, or filesystem writes. Real PC-88VA SCSI boot remains excluded because
there is no SCSI BIOS; the future SCSI profile is data-only through one external
`DEVICE=` driver. SASI/SCSI runtime and hardware are NOT RUN. Hardware status is
**DEFERRED HARDWARE VALIDATION**.

## Next actions

1. Commit the reviewed M17 source/build candidate locally, then execute the
   complete clean double build from its exact committed allowlisted inputs.
   Fix any build, test, placement, or acceptance-verifier defect and repeat the
   affected gates.
2. Keep guest CONFIG QA explicitly NOT RUN unless an authorized, identified
   VAEG firmware environment is available; do not infer it from host tests.
3. Reconcile the report and M19 SASI/M21 external-SCSI handoffs, complete
   privacy and bounded-diff review, then publish the parent topic and verify
   exact-tip CI, remote equality, and child-before-parent reachability.

The accepted M16 archive remains unchanged. This report contains no
self-referential future publication SHA or unrun guest/hardware claim.
