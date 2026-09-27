# M16 host tooling

The M13 carrier builder and linked-placement verifier in this directory are
maintained M16 copies of the algorithms from parent revision
`1af9974700cd4dd1164cc0df56cc062925376148`:

- `tools/m15/build_compressed_kernel.py`
- `tools/m15/verify_linked_placement.py`
- `tests/m15/test_memory_placement.py`
- `tests/m15/test_carrier_tail.py`
- `config/m15/legacy-placement-test.json`

Their M16 regression copies are under `tests/m16/`. They are retained because
the active M16 kernel still uses the M13 carrier and placement contract. The
M16 copies operate on the pinned component inputs and local fixture
`config/m16/va-fixed-loader-profile-test.json`; they do not import, execute,
or read any M15 runtime files. Generated test output belongs under `build/m16/`.

This provenance records algorithm lineage only. M15 acceptance results and
unrelated M15 tooling are not carried into M16.

The overlay loader builder and profile validator are M16-maintained copies in
`tools/m16/build_loader.py` and `tools/m16/loader_profile.py`. Their source
provenance is fdkernel commit
`d8dbbf7111f86ea4800daeac84ac53ba601aaf32`,
`components/fdkernel/pc88va/tools/{build_loader.py,loader_profile.py}`.
`tests/m16/test_loader_builder.py` exercises those local copies. M16 does not
import component helper tools or run the component's historical milestone
tests as part of its build.

## Build

The host needs Git, Python 3 with pip, Docker Buildx, and network access for the
first acquisition of pinned public dependencies. Build the locked Linux/amd64
Open Watcom 1.9 image, then build the complete disk twice from Git archives:

```sh
python3 tools/m16/toolchain.py
python3 tools/m16/build_image.py --output build/m16-image
```

`build_image.py` downloads the configured Unicorn 2.1.4 verifier wheel and
checks its filename and SHA-256 before starting network-disabled containers.
Both builds use the committed parent inputs, exact component gitlinks, and the
image produced by `toolchain.py`; their full artifact manifests must match.
The output directory must stay Git-excluded. `build/m16-image/media.d88` is a
freshly composed candidate and is not a milestone distribution until its guest
acceptance and publication checks are complete.

## Runtime memory and kernel placement

See the [current memory contract](../../docs/porting/m16-memory-layout.md) for
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

### Boundary data fixtures

Generate original FAT12 files that cross tracks and end in the final data
cluster with this milestone's own producer and independent inspector:

```sh
python3 tools/m16/build_floppy_media.py --boundary --output build/m16-boundary-media
```

Each of the five profiles contains `PATTERN.BIN` (33,792 bytes). Its final
cluster is moved to the end of the data area, leaving a discontinuity in the
FAT chain. The file fills that cluster, so a complete guest copy reads the
last data sector as well as ordinary track/head boundaries. The manifest
records exact image hashes and cluster chains. This command establishes host
fixture validity only; DOS read/write and fresh-process persistence require
separate guest qualification with disposable copies.
