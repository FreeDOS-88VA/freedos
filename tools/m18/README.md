# M18 build, DOS payloads, and media tooling

M18 owns its complete parent-side build orchestration, helper modules,
producers, inspectors, settings, tests and fixtures under `tools/m18/`,
`config/m18/` and `tests/m18/`. `make m18-disk` exports the exact committed
M18 input paths and the exact pinned component gitlinks, checks them in an
allowlist-only Linux/amd64 container with networking disabled, builds every
program from source, composes and independently reads back a new native 2HD
D88, then repeats the whole build in a second clean container. No candidate
D88, generated DOS executable, ROM, private firmware, private disk, guest trace,
or prior milestone tool/config/test directory is a build input.

## Build interface

- `make m18-toolchain` prepares or verifies the pinned Linux/amd64 Open Watcom
  1.9 container. The official tool archive, Ubuntu base, apt snapshot, compiler
  identities and host test wheel are pinned.
- `make m18-disk` performs both complete source builds, compares D88 bytes and
  release records, validates payload hashes/FAT chains and root-directory
  capacity, and writes `dist/m18/` without overwriting an unrelated existing
  distribution. A repeat with the same inputs is allowed only if every public
  distribution file is identical. Use `M18_DIST=dist/m18-candidate-<id>` for a
  changed source identity.
- `make m18-clean` removes only the marker-validated Git-excluded `build/m18/`
  intermediate root. It preserves `dist/m18/`, the identity-pinned toolchain,
  and the host wheel cache.
- `make m18-host-tests` downloads/verifies the pinned Unicorn 2.1.4 wheel in
  the Git-excluded cache and runs the M18-local suite on Linux/x86_64. On other
  host architectures, `make m18-disk` runs all tests inside its pinned
  Linux/amd64 build container.

The topic branch must be committed and clean before `make m18-disk`. The build
checks the exact baseline ancestry, component gitlinks, source-archive hashes,
and fork/upstream URL identities. If a component checkout lacks its public
`upstream` remote, the script adds the exact URL from the committed lock to that
checkout's local Git configuration; it never changes component source or pushes
to a remote. Parent build inputs are exported from Git, not the mutable working
tree.

## Milestone-local layout

- `build_image.py`, `build_image.sh`, and `finish_image.py` own the complete
  clean build and output records.
- `build_loader.py`, `loader_profile.py`, `build_compressed_kernel.py`,
  `verify_m13_linked_placement.py`, `media.py`, and `compose_image.py` are
  maintained M18-local copies of the required algorithms at M18 start. Their
  M17 and M13 source lineage is documented in the files. Only M18 tests and
  configuration are used here; no earlier parent milestone is imported.
- `edlin/`, `assembler/`, `memmap/`, `programs/`, and `maintenance/` contain
  source builders for EDLIN, real-mode JWASMR, MEMMAP, MORE, and the three
  profile-bounded maintenance applications. All application code targets
  8086 real mode; the native VA loader/kernel remains platform-specific.
- `manifests/m18-components.lock.json` pins the exact public kernel, FreeCOM,
  COUNTRY.SYS, EDLIN and JWasm gitlinks and source-archive hashes. The shared
  `manifests/toolchains.lock.json` supplies identity-pinned compiler and
  toolchain dependencies.
- `verify_isolation.py` rejects any earlier milestone directories, path
  references, symlinks or transitive code dependencies from the allowlisted
  export. `verify_source_audit.py` rejects private/generated-media inputs and
  checks the public source/package lock.

The fixed 2HD output is 80 cylinders × 2 heads × 8 sectors/track × 1024 bytes,
FAT12, 1280 sectors, 192 root entries, one-sector clusters and a single boot
volume label. The media composer allocates the stage-2 loader contiguously for
the native boot code, writes all file bytes from the fresh source-build
payloads, emits fixed FAT timestamps, and verifies exact D88/FAT readback.
`capacity-budget.json` is a host allocation record and policy floor, not a guest
measurement of the complete edit/assemble workflow.

## Tool scope and limits

The disk has the native boot loader/kernel, FreeCOM, COUNTRY.SYS, EDLIN, MORE,
MEMMAP, JWASMR, CHKDSK, FORMAT and SYS, plus English/ASCII starter sources and
license notices. `packages.json` records version, source, license, CPU, build
options, VA-specific adaptation and gate status; generated `package-manifest`
records add exact hashes and DOS MZ allocation data.

MEMMAP discovers the MCB list through the pinned FreeDOS interface, validates
DOS version/layout and PSP ownership, shrinks only its own MZ block, and reports
managed DOS MCB accounting. It explicitly labels physical/reserved memory as
unavailable. CHKDSK is read-only. FORMAT writes filesystem metadata only to a
B: volume with a readable, valid native 2HD BPB from prior preparation. SYS
installs validated native boot files to prepared B: media and writes the boot
sector last. None of the
maintenance commands supports other floppy profiles, SASI/SCSI, hard-disk
boot, or FAT16.

Host success does not establish DOS runtime behavior, free-memory ownership,
VAEG compatibility, guest RAM minima, disk-space peak use, or hardware support.
The required shell, editor, pager, memory map, assembler, sample workflow and
maintenance operations must be qualified against the exact output D88 before
M18 completion. Every report must name guest/emulator/hardware gates that were
not run; a clean link or synthetic CPU test is not a substitute.
