# M17 source build

M17 starts from the accepted M16 parent tip
`f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4`. Its source lock records the exact
M16-derived component inputs and the M17 CONFIG/INIT integration candidate.
A recovered M17 branch based on the obsolete `fc891f3cd424c281680dd15b3f269bef4a4d2880`
is audit history only; its status and acceptance are not inherited. No build
step imports, executes, or reads another milestone's tools/config/tests tree.

# M17 host tooling

The M13 carrier builder and linked-placement verifier in this directory are
maintained M17-local copies of algorithms from parent revision
`1af9974700cd4dd1164cc0df56cc062925376148`:

- `tools/m15/build_compressed_kernel.py`
- `tools/m15/verify_linked_placement.py`
- `tests/m15/test_memory_placement.py`
- `tests/m15/test_carrier_tail.py`
- `config/m15/legacy-placement-test.json`

Their M17 regression copies are under `tests/m17/`. They are retained because
the active M17 kernel still uses the M13 carrier and placement contract. The
M17 copies operate on the pinned component inputs and local fixture
`config/m17/va-fixed-loader-profile-test.json`; they do not import, execute,
or read any M15 runtime files. Generated test output belongs under `build/m17/`.

This provenance records algorithm lineage only. M15 acceptance results and
unrelated M15 tooling are not carried into M17.

The overlay loader builder and profile validator are M17-maintained copies in
`tools/m17/build_loader.py` and `tools/m17/loader_profile.py`. Their source
provenance is fdkernel commit
`d8dbbf7111f86ea4800daeac84ac53ba601aaf32`,
`components/fdkernel/pc88va/tools/{build_loader.py,loader_profile.py}`.
`tests/m17/test_loader_builder.py` exercises those local copies. M17 does not
import component helper tools or run the component's historical milestone
tests as part of its build.

## Build

The host needs Git, Python 3 with pip, Docker Buildx, and network access for the
first acquisition of pinned public dependencies. Unicorn is used only by the
maintained real-mode placement/carrier regressions; it is not the guest emulator
and is not VAEG. Build the locked Linux/amd64
Open Watcom 1.9 image, then build the complete candidate twice from Git archives:

```sh
python3 tools/m17/toolchain.py
python3 tools/m17/build_image.py --output build/m17-image
python3 tools/m17/verify_acceptance.py --build build/m17-image
```

`build_image.py` downloads the configured Unicorn 2.1.4 verifier wheel and the
pinned JSON Schema validator wheels, checks every filename and SHA-256, then
starts network-disabled containers.
Both builds use the committed parent inputs, exact component gitlinks, and the
image produced by `toolchain.py`; full artifact manifests, including the QA
startup disks and six storage fixtures, must match byte-for-byte. The output
directory must stay Git-excluded. `build/m17-image/media.d88` is an M17
regression candidate, not a new milestone distribution; only the unchanged
accepted M16 archive is designated.

## Runtime memory and kernel placement

See the [current memory contract](../../docs/porting/m17-memory-layout.md) for
ownership, temporary lifetimes and the required qualification scope.

At startup, immediately after its source SHA-1, the kernel prints measured
conventional memory and its effective placement addresses. The adapter restores
one byte after testing it with 00h and FFh at each 1 KiB boundary from 256 KiB
up to the conventional-memory ceiling of 640 KiB. It also checks the final byte
below 256 KiB as a minimum-capacity guard. This is a capacity sample, not an
exhaustive RAM integrity test. Neither the loader nor the kernel reads backup
RAM to determine, cap, or provide a fallback for conventional-memory capacity.
DOS uses the measured contiguous capacity, independently of retained BIOS
selections; firmware setup or a backup-memory update is not a prerequisite.

`CONFIG.SYS` may contain the pre-kernel directive `PC88VA_LOADSEG=2000` (hexadecimal
paragraph address, optionally suffixed with `h`). It selects the expanded kernel
layout base: 2000h means physical address 20000h. The default is 1000h/10000h.
This is the beginning of the entire resident kernel, including its C code and
data. `Resident asm` in the display is an internal relocated assembly-code
part of that resident kernel, not a second meaning of LOADSEG.
The resident prefix contains code, data and the bounded NEAR work arena.
Resident assembly follows that prefix. Final FAR kernel work (buffers, file
and drive tables, and configured stacks) is allocated consecutively immediately
after resident assembly through the upstream system-block/sub-MCB mechanism.
Only paragraph alignment and owned MCB metadata separate these allocations.
A startup invariant checks that the resident end equals the system-block start,
that the work end equals the next free MCB, and that the free block reaches the
temporary reservation. The display reports `Kernel low`, `Kernel work`, and
`DOS free begins`; the free address excludes its MCB header.

Before its first disk read, stage 2 measures RAM and derives file/MZ staging
as `RAM_end - 19000h`, history ring as `RAM_end - 8000h`, and bridge stack
top as `RAM_end - 10h`. AX passes measured KiB and CX passes staging to the
carrier. The complete expanded input image and bootstrap stack must fit below
staging. The carrier rejects unsafe LOADSEG values before expansion.
Loader code, stack and metadata use their qualified low intervals until handoff.

INIT and its 4 KiB stack are temporary. Their combined end is
`RAM_end - 2000h`; INIT starts at that end minus its aligned linked size and
4 KiB. They follow measured RAM independently of LOADSEG. Every INIT segment
fixup and the runtime descriptor uses this same address. This replaces both
the old fixed INIT slot and the unpublished conditional low-INIT experiment.
The builder binds the carrier to the exact loader/workspace profile and checks
all simultaneous lifetimes, including the history ring and bridge stack.

Early filesystem buffers grow below temporary INIT. Once final low kernel work
has been allocated and all pointers replaced, P_0 switches to its permanent
stack, frees the temporary MCB and joins adjacent free memory before starting
COMMAND.COM. INIT is never retained as a hole in the final conventional arena.
Moving INIT alone does not change the size of final resident work. The final
resident base is the explicit safe lower bound supplied by LOADSEG; writable
RAM measurement supplies capacity, not ownership of firmware memory.

RAM-dependent fixes require the failing persisted configuration, alternate-model
coverage, and a working-capacity control before a replacement is described as
verified. See `AGENTS.md` for the evidence and handoff requirements.

## M17 configuration and storage

See [configuration support](../../docs/porting/m17-configuration.md),
[storage contracts](../../docs/porting/m17-storage-contracts.md), and the
[M17 report](../../docs/porting/m17-report.md). The candidate disk includes an
editable CONFIG.SYS. The common parser and DEVICE= path are present in the
candidate source. The exact-candidate VAEG guest checks are recorded in the
report and configuration
document; they qualify the listed FDD boot/CONFIG/INIT cases only. They do not
qualify SASI/SCSI runtime or guest access to any HDD fixture. PC88VA_LOADSEG is
still consumed by the earlier loader. Explicit platform limitations are
documented.

The full build also emits `run-1/storage-media/` and independently reads back
all six data fixtures. These HDD images are nonbootable host fixtures, with no
claim of SASI/SCSI guest support. `run-1/config-qa/` contains separate pristine
CONFIG.SYS/FDCONFIG.SYS startup candidates for default parsing, FDCONFIG
precedence, positive character-driver INIT, zero-unit block-driver INIT, and
`PC88VA_LOADSEG=2000` through the real loader path. They are QA inputs, not
normal-use media. Standalone storage-fixture reproduction:

```sh
python3 tools/m17/produce.py --profiles config/m17/media-profiles.json --output build/m17-storage
python3 tools/m17/inspect_storage.py --profiles config/m17/media-profiles.json --directory build/m17-storage
```

Only Python's standard library is required for standalone fixtures. The full
kernel/shell build uses the pinned Linux/amd64 Open Watcom 1.9 container plus
identity-pinned Unicorn and JSON Schema verifier wheels. Docker is the Linux host runtime. No other milestone's directory or private input is read.
The shared compatible image tag still contains `m16`; it identifies the locked
toolchain, not a runtime dependency on M16. No new dependency installation is
needed on the current Ubuntu host.

`SYS.ID` retains the `M16SOURCE` token required by the pinned SYSVA component;
this is a component interface marker, not the current milestone identity.
Qualification utilities CFGDEV.SYS, CFGNONE.SYS, CFGPROBE.COM, CFGSTATE.COM
and CFGMEM.COM are built from `tests/m17` sources. CFGDEV is a disposable
character device; CFGNONE is a zero-unit block-device negative case. Neither is
a storage controller or production SCSI driver. Run the exact QA image/profile
listed in `run-1/config-qa/manifest.json`; preserve each pristine image and record
its digest separately from any VAEG-mutated runtime copy. SCSI boot is excluded:
the owner confirms real PC-88VA hardware has no SCSI BIOS, so SCSI is data-only
through a future external `DEVICE=` block driver.
