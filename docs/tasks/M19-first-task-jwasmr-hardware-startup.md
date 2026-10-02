# M19 entry task: JWASMR hardware startup

Status: **DONE IN M19 — HARDWARE PASS** (owner report, 2026-10-02): on the M19
public checkpoint disk, JWASMR with no arguments shows Usage on the physical
machine, and HELLO.ASM assembles. Cause addressed: the Open Watcom 1.9
pre-main x87 probe began with FWAIT; M19 links a no-WAIT probe instead. See
`docs/porting/m19-report.md`.

The owner accepts M18 for release as **emulator-validated only**, with its
unchanged designated disk and exact bounded HOST/VAEG evidence. JWASMR's
reported real-machine hang is a known issue, not a repaired M18 result.

## First priority, before SASI-data work

Investigate and fix the report that a no-argument JWASMR invocation on physical
PC-88VA hardware hangs before Usage appears, although it returns and assembles
the small sample in VAEG. Do not presume faulty RAM or silently promote
emulator success to hardware compatibility. Public issue material must omit
private ROM/media identities, paths, traces and runtime-derived values.

Before implementation, bind the actual M18 release tag/publication tip,
qualified implementation, component gitlinks, build/toolchain identities and
required exact-head CI. Preserve M17 storage contracts and the M18 failing
disk/private report. Establish the actual failing model/configuration and
executable/media identity; distinguish installed RAM from retained selection.

## Source review leads, not an established cause

The released Open Watcom startup contains a pre-main software-FPU initializer
that calls a raw x87 detector with WAIT/FWAIT before installing emulation
vectors or honoring NO87. The linked clock initializer also assumes an IBM
BIOS data-area counter. Review the exact linked instructions, initializer
ordering and platform interfaces rather than treating library presence as
proof of no-coprocessor hardware safety. The absent-FPU emulator model does
not qualify the physical POLL/TEST signal contract.

A platform integration repair must preserve actual software floating-point
conversion and selected FreeDOS behavior. Project-owned adapter/build inputs
belong in M19-local tooling/config/tests; component changes belong in their own
public component repositories/branches, followed by verified public gitlinks.
Do not patch a saved executable or change the separate VAEG checkout merely
to make the report disappear.

## Required closure

- Clean-build the complete changed candidate from pinned public inputs and
  compare two independent disks; run M19-maintained startup/negative tests.
- Qualify affected VA/VA2 emulator workflows, including no-argument Usage,
  small COM/MZ assembly and execution, software real-number conversion,
  error/repeat behavior and DOS ownership recovery. Retest affected installed
  versus retained capacity cases, without mistaking MCB checks for RAM tests.
- Test the exact changed candidate on the **reported physical configuration**
  before claiming that the real-machine hang is fixed. Preserve private
  identity-bound observations and describe unavailable tests as NOT RUN.
  An emulator-only candidate is not a verified physical repair.
- Record the actual outcome and remaining limitations; no hardware test that
  was not run receives HARDWARE PASS.

After this first task, M19 retains its planned SASI HDD **data-drive** scope
and M17/M18 dependencies. This priority note does not implement SASI, change
milestone numbering or qualify M18 hardware support.
