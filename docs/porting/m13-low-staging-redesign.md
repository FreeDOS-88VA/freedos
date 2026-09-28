# M13 PC-88VA low staging redesign

Historical M13 design snapshot: references below to the then-current worktree,
fixed placement or unresolved lifetime dependencies describe that stage only.
For active M16 behavior and qualification, use [the M16 memory contract](m16-memory-layout.md).
Historical status and results below are preserved, not transferred to M16.

Status: implemented in the current dirty M13 worktree; component and parent
publication/qualification are not claimed.

## Placement contract

The PC-88VA loader profile derives the assembler define
`PC88VA_LOW_STAGING_SEGMENT` from the validated `kernel_file` ownership
interval.  The profile requires that interval to be paragraph aligned and
requires the exact `kernel_file == kernel_allocation` alias for in-place low
staging.  The current common envelope is segment `3000h`, physical
`30000h..3fff0h` (end exclusive).  Its end is below the `40000h` limit of a
256 KiB machine, so the same fixed envelope is valid for 384, 512 and 640 KiB.

The emitted define is consumed by `stage2.asm`; the source refuses to build
if it is absent or differs from `S2_KERNEL_FILE_SEGMENT`.  It is an assembler
profile contract, not a guest `CONFIG.SYS` setting and not a hard-coded DOS
arena limit.

Stage-2, loader stack, scratch, firmware and the resident destination remain
separate ownership intervals.  At 256 KiB, INIT is split below the staging
envelope and its temporary stack is bounded before the one-way handoff.  The
in-place carrier uses a forward overlap-safe MZ body compaction.  Its temporary
far-return frame is placed in the rounded zero-filled carrier tail, rather
than the historical `0400h` stack position that overlaps the compacted body.

## Files

- `config/m08/low-staging-overlay.json`: synthetic profile exercising the
  common low envelope.
- `components/fdkernel/pc88va/tools/loader_profile.py`: profile validation and
  `PC88VA_LOW_STAGING_SEGMENT` emission.
- `components/fdkernel/pc88va/boot/stage2.asm`: low-staging metadata and
  protected-prefix contract.
- `components/fdkernel/pc88va/boot/mz_validate.inc` and `mz_transform.inc`:
  exact in-place validation and MZ body compaction.
- `components/fdkernel/pc88va/kernel/m13_unpack.asm`: in-place bridge path and
  separate bridge stack.
- `tools/m13/build_compressed_kernel.py`: fixed carrier defaults, capacity
  checks and bootstrap-frame placement.

## Verification

The ROM-free Linux/amd64 container run used NASM and Unicorn 2.1.4.

- loader build-loader, stage1 and stage2 tests: **29/29 PASS**;
- stage2 includes both ordinary and low-staging entry/return paths;
- placement tests: **17/17 PASS**;
- low overlay JSON Schema validation: **PASS**;
- two clean stage2 builds per profile: byte-identical;
- low stage1/stage2 assembly from `low-staging-overlay.json`: **PASS**.

Host arm64 Unicorn execution was not used; it terminates with the known
unsupported native execution failure.  No VAEG or physical PC-88VA run is
claimed by this redesign record.  The current source remains dirty and no
commit or D88 was produced by this bounded placement change.
