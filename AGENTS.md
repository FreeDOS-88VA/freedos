# Agent Rules

For future local Colima profiles, use `tools/host/colima.sh`. It keeps VM
disks and configuration in this repository's Git-excluded `.colima/`, rather
than the user's home directory. Keep an active milestone's existing runtime
until its work is complete, and retain required image exports before removal.

This repository integrates and pins components; component source remains in
its component repository. If component source must change, work in that
component's own repository and branch, commit there, and then update the
parent gitlink. Never vendor a submodule file as a copy in the parent.

The `origin` remote for the kernel and FreeCOM components is the
`nakatamaho` fork. Their `upstream` remote is the corresponding `lpproj`
repository. Do not push directly to an upstream branch. Preserve provenance
and exact source SHAs in the parent metadata.

For the PC-88VA port, keep the selected upstream FreeDOS behavior as the DOS
implementation baseline. MS-DOS references can inform API review but do not
require exact MS-DOS behavior or changes solely to match it. Do not repair an
existing upstream FreeDOS bug as part of the port; record it when relevant and
leave the upstream behavior intact. Fix defects introduced by the VA adapter,
platform integration, or port-specific configuration. Do not add behavior to
turn the project into a separate DOS implementation. Keep public issue reports
free of private ROMs, media, traces, paths, and derived values.

Do not commit private artifacts or facts derived from private artifacts. Do not
change the separate VAEG checkout. PC-98 behavior is a structural precedent,
not PC-88VA evidence.

The owner clarified the public build boundary: project-authored platform
adapters, memory-layout settings, and BIOS call interfaces needed to build
the port are source inputs and must be versioned. Do not classify these as
private merely because they were tested against private media or firmware.
ROM contents, private disk contents, raw observations, and trace payloads
remain excluded. New media builds must not depend on old candidate disks or
saved DOS executables; generate payloads and filesystem structures from the
committed sources and explicit public configuration.

## Reproducible milestone distributions

### Milestone-local tooling from M15 onward

For M15 and every later milestone, keep the complete host build and media
toolchain orchestration, helper modules, producers and inspectors within
`tools/mNN/`. Own its milestone-specific settings under `config/mNN/` and its
fixtures/tests under `tests/mNN/`. Do not import, invoke, or read runtime inputs
from another milestone's `tools`, `config`, `tests`, or `containers` directory,
including through wrappers, symlinks, modified search paths, or transitive
imports. Removing historical milestone directories must not break the active
milestone's build, SYS-target preparation, or required verification.

When retaining an earlier parent-owned algorithm, commit a maintained local
copy of the needed implementation and its tests with provenance; do not carry
forward its historical acceptance state or unrelated build dependencies.
Component source still belongs in its own pinned component repository: never
copy component source into the parent to satisfy this rule. Shared public
toolchain identity locks, repository license files, standard host tools, and
the prescribed Colima host wrapper may remain milestone-neutral dependencies.
An old name inside a pinned component interface or compatible image tag does
not authorize a dependency on the old parent milestone's directories.

Before publication, execute the complete clean build from an allowlisted
source export containing the active milestone's inputs and its explicit
milestone-neutral dependencies, with other milestone directories absent.
Check media preparation and readback through that milestone's own helpers.
Fix any direct or transitive dependency discovered by this check before
publishing. Apply this rule to M15 onward; do not rewrite or delete M00-M14
history merely to make a current build pass.

This is a continuous requirement for the active milestone, not only a release
gate. At every published work checkpoint, the entire current milestone must
be clean-buildable from a fresh checkout of its pushed public Git revision
and pinned public dependencies. This includes all component builds, platform
adapters, loaders, required support programs, configuration, and final media
composition within that milestone's scope; building only an individual
component or reconstructing a disk from saved binaries is insufficient.

Keep the complete build entry point, recipes, source pins, configuration,
dependency acquisition instructions, and usage documentation committed and
pushed together with the work they enable. Push component commits before
publishing parent gitlinks. Local-only commits, untracked helpers, private
inputs, and cached outputs must never be required to reproduce a published
checkpoint. Maintain a usable published build throughout milestone work; do
not postpone this obligation until PASS, a human gate, or final archiving.

Verify build-affecting changes with a clean build from the exact public inputs.
If any step of the full milestone build fails or depends on unpublished
material, fix the source, recipe, configuration, dependency setup, or
documentation as appropriate, then repeat the affected clean build through
the final artifact. Publish the correction and verify its source binding.
Do not treat the error as documentation-only, work around it with an old D88
or saved executable, or report the milestone as rebuildable while the error
remains. If an external blocker cannot be resolved, identify it explicitly
and retain the last verified public build checkpoint without claiming success.

Every milestone distribution D88 must be clean-buildable using public inputs
only: committed source, pinned component gitlinks, committed configuration,
and publicly obtainable, identity-pinned toolchains and dependencies. A fresh
checkout must be sufficient after the documented toolchain setup. Never
require private JSON, ROMs, previous milestone D88s, saved DOS binaries,
untracked scripts, or another developer's build directory to generate it.
Keep any ROM-dependent emulator verification separate from the build.

Commit and push the complete build recipe and required public settings before
designating the distribution. Build in clean exported source trees, verify
two independent builds produce identical D88 bytes, and preserve the exact
parent/component commits and toolchain identities. Normalize only explicitly
documented non-semantic build metadata; do not conceal binary differences.
Do not use unavailable private inputs as an excuse to archive an irreproducible
milestone image. Fix the build recipe first.

The owner authorizes public distribution and Git storage of these images.
As an explicit exception to the generated-artifact prohibitions in this file,
archive the designated D88 with xz under `images/milestones/mNN/`. Commit its
compressed and uncompressed SHA-256 hashes, byte sizes, exact source/build
identities, clean rebuild and extraction instructions, applicable license
notices or references, and the actual validation scope alongside it. Verify
decompression reproduces the designated D88 exactly. Retain one designated
distribution per milestone; never substitute private test disks or commit
intermediate build products. A published image is not automatically a new
VAEG or hardware PASS.

Use these evidence labels precisely: `HOST PASS`, `VAEG PASS`, `HARDWARE PASS`,
and `DEFERRED HARDWARE VALIDATION`. Real hardware is optional and non-blocking,
but only an actual hardware result can receive `HARDWARE PASS`.

Except for the designated milestone archives described above, do not commit
generated files, build products, images, or logs. Use English for code,
comments, and file names. Fail closed: an unrun test is not a success.
M00 permits scaffold and provenance work only. M01 permits the parent
repository build harness and reproducibility evidence for pinned component
exports. The approved M01F exception is one fdkernel child commit that changes
only WMake conditional syntax; it must not add PC-88VA source changes,
packages, images, emulator tests, or hardware tests.

M01 builds must run in the pinned Linux/amd64 container, never in a component
submodule or a host bind-mounted source tree. The kernel, FreeCOM, and
COUNTRY.SYS sources are exported with deterministic git archives. The two
kernel/FreeCOM fork remotes remain `origin=https://github.com/nakatamaho/...`
and `upstream=https://github.com/lpproj/...`; component source changes belong
in the component repository and branch before the parent gitlink is updated.
The parent must preserve exact component, source-archive, contract, and
toolchain identities.

The canonical Open Watcom binaries used by M01 are the official final 1.9
Linux i386 tools in `/opt/openwatcom-1.9/binl`, executed inside the pinned
Linux/amd64 container. They are not run directly on macOS. On Apple Silicon,
the complete x86_64 QEMU Colima profile is only a host adapter: the actual
container must report `x86_64` and `amd64`, while daemon and adapter details
remain diagnostic evidence.

M01 required builds disable UPX. Do not commit toolchain archives, generated
binaries, results, logs, ROMs, BIOS files, disk images, private artifacts, or
private-derived facts. Do not report skipped VAEG or hardware work as a pass.
The exact evidence labels remain `HOST PASS`, `VAEG PASS`, `HARDWARE PASS`, and
`DEFERRED HARDWARE VALIDATION`; M01 can use only `HOST PASS` after its local
gates and native x64 GitHub Actions gate pass. VAEG and hardware are `NOT RUN`.

## Milestone acceptance and handoff

Keep START_SHA, QUALIFIED_IMPLEMENTATION_SHA, PUBLICATION_TIP_SHA, and
DOWNSTREAM_BASE_SHA distinct, as full 40-hex identities. Before implementation,
fetch the named predecessor branch, verify its exact required tip and ancestry,
inspect its bounded publication diff, verify exact clean component gitlinks,
validate actual prerequisite evidence and bindings, and check required CI run
attempts, successful jobs, and exact tested head SHAs. Never substitute a pin.
An explicit owner-authorized fresh private prerequisite may replace an
unavailable historical private bundle; never call that historical recovery or
change the predecessor's public acceptance state merely because its private
bundle is unavailable.

A digest establishes identity, not semantic validity. Validate schemas as
schemas and actual JSON instances against them, close referenced evidence and
artifact dependencies, and test missing/unknown fields, malformed hashes,
digest drift, incomplete references, topology, and stale CI claims negatively.
Rebind changed evidence in dependency order: schema, manifest, golden,
qualification, contract, verifier pins, acceptance metadata. Do not hide drift.

Provide preflight, clean build, two-build comparison, instance validation,
negative tests, historical regression, privacy audit, and final acceptance
operations. Local and native CI must call the same acceptance verifier.
Use focused child commits, push and verify child reachability before updating
the parent gitlink. Keep exact source and toolchain provenance.

PASS and HANDOFF READY are separate. Qualify the implementation and its CI,
then publish only acceptance metadata, the report, non-behavioral documentation,
or Make help. Any behavioral/source/schema/contract/golden/verifier/workflow or
gitlink change requires affected qualification gates and CI again. Verify the
publication tip's own CI, remote equality, ancestry, and bounded publication
diff before handoff. A committed report cannot contain its own SHA: record
the exact final publication tip and downstream base in the post-push handoff.

Every milestone outcome, including partial or blocked, requires a saved
docs/porting/mNN-report.md with status, relevant commits, verification,
unresolved work, and explicitly unrun gates. Retain canonical private evidence
in persistent Git-excluded storage. Never publish private inputs, identities,
paths, raw traces, or concrete derived values. Unrun hardware is NOT RUN.
Fix recoverable harness, build, portability, and CI defects within the task.

For PC-88VA startup or kernel changes in the active milestone, treat the linked
image, generated
placement descriptor, MZ carrier, measured conventional-memory ceiling, INIT stack,
resident text boundary, and startup banner as one layout contract. Any change
that can alter the kernel bytes, linker map, section grouping, carrier input,
or descriptor must rebuild from clean pinned inputs and rerun the carrier and
linked-placement verifiers plus that milestone's maintained placement tests. Inspect the
generated descriptor against the exact map and verify its version, image,
resident, INIT, stack, and dynamic-or-explicit memory-top fields before
accepting the build. A prior boot result applies only to the exact kernel
identity and configuration that was tested; do not infer bootability from a
successful link, image hash, or a run of another candidate. Do not repeat an
unchanged RAM-size matrix to diagnose the same startup failure: identify and
fix the source-level contract first, then boot the changed candidate in the
reported failing mode and configuration. Preserve recorded results and never
claim an unrun mode or configuration passed.

For variable-RAM PC-88VA carriers, calculate the minimum runtime capacity from
every live loader, carrier, scratch, expanded-image, INIT, and initial-stack
interval. A runtime-detected DOS arena ceiling does not make an early fixed
interval safe on a smaller machine. Bind the carrier profile to its loader
profile and verify that the installed and measured 256, 384, 512, or 640 KiB
capacity is supported before calling that capacity passed. When a low-memory
profile is required, qualify its matching in-place loader and carrier together;
do not transplant only the kernel carrier across incompatible profiles.

For every active milestone, distinguish installed physical RAM from the RAM
capacity retained in BIOS backup memory. The VA loader and kernel must measure
writable conventional RAM at boot; they must not read backup RAM to determine,
cap, or supply a fallback for that capacity. Do not require a firmware setup
session or a backup-memory update before FreeDOS can detect installed RAM.
Retained selections are regression-test inputs only, not a memory-size source.
A saved selection is not proof that the corresponding RAM is writable.
Changes to RAM detection, DOS arena sizing,
or loader/carrier placement must cover both matching settings and a stale
selection larger than installed RAM, including 512 KiB installed with a retained
640 KiB selection. The adapter must bound or reject an unavailable arena before
constructing its MCB chain. Decoder-only tests with fully mapped RAM do not
qualify this contract. Host regressions must model unavailable/read-only RAM
and verify that any capacity probe restores sampled memory, registers, flags,
and bank mappings.

Before handing over a replacement disk for a reported RAM-dependent failure,
clean-build the exact candidate and boot it in the reported machine model and
RAM configuration, including persisted settings that trigger the failure.
Record installed capacity and retained selection separately in private evidence,
together with exact disk and emulator identities. Verify shell startup, COM/MZ
execution, and guest file write/readback. Qualify affected alternate models and
a previously working capacity as regression controls. Preserve the failing
candidate and evidence; do not substitute a fresh backup-memory state for the
reported configuration or infer this coverage from a successful link, decoder
test, or boot at another capacity. If the failing configuration was not run,
state that explicitly and do not describe the replacement as verified for it.

`PC88VA_LOADSEG` selects the paragraph address of the expanded resident kernel
and the consecutive kernel work area. The temporary KERNEL.SYS buffer and INIT
follow the measured RAM-top workspace plan. Keep this meaning consistent in the
loader, carrier, startup display, documentation, and tests. A changed base must
translate all affected resident segment relocations,
placement records and bootstrap stack together. Temporary INIT and its stack
follow measured RAM top independently; bind their segment fixups and descriptor
to the same effective placement. Final kernel work must follow the resident
hull consecutively, with only paragraph alignment and owned MCB metadata.
Check this adjacency and release temporary allocations before starting the shell.
Qualify a non-default setting through the actual CONFIG.SYS loader path and
reject an unavailable or overlapping layout before expansion. Display measured
conventional RAM and effective layout addresses from the runtime records.

The active M17 memory contract is `docs/porting/m17-memory-layout.md`; its
required gate is recorded in `docs/tasks/M17-storage-contracts-media-formats-goal-Codex.md`.
Historical M13-M16 sizing instructions and capacity results remain history and
do not override it. Writable capacity does not establish free-memory ownership
or a safe lower bound. Keep the LOADSEG lower-bound policy explicit. Validate
INIT numeric diagnostics against the actual linked formatter with SS different
from DS, and preserve the qualified VA stack-pointer/compiler contract.

INIT executes with SS different from DS. Never pass an INIT stack-local buffer
through a NEAR pointer to memset, strcpy, memcpy or another DS-based helper.
Use explicit SS-based FAR pointers and matching FAR operations, or omit code
that is unreachable under the VA platform policy. Audit this when shrinking
DGROUP: removing unrelated arrays can expose an existing wrong-segment write
against live allocation metadata. Preserve release-barrier error returns and
keep their diagnostics resident.

The M17 kernel configuration passes are enabled. The loader reads only the
PC88VA_LOADSEG selector; it does not replace DOS CONFIG.SYS processing. Preserve
FDCONFIG.SYS precedence in the common kernel, and qualify settings through actual
startup. Do not restore the historical M13 early return or classify disabled
functionality as unused merely to shrink memory. Track unavailable native options
explicitly and keep ordinary DOS parsing separate from platform BIOS interfaces.
