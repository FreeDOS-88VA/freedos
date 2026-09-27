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

At startup, immediately after its source SHA-1, the kernel prints measured
conventional memory and its effective placement addresses. The adapter restores
one byte after testing it with 00h and FFh at each 1 KiB boundary from 256 KiB
up to the conventional-memory ceiling of 640 KiB. It also checks the final byte
below 256 KiB as a minimum-capacity guard. This is a capacity sample, not an
exhaustive RAM integrity test. Retained BIOS selections do not replace the
measurement. DOS uses the measured contiguous capacity.

`CONFIG.SYS` may contain the pre-kernel directive `PC88VA_LOADSEG=2000` (hexadecimal
paragraph address, optionally suffixed with `h`). It selects the expanded kernel
layout base: 2000h means physical address 20000h. The default is 1000h/10000h.
This is the beginning of the entire resident kernel, including its C code and
data. `Resident asm` in the display is an internal relocated assembly-code
part of that resident kernel, not a second meaning of LOADSEG.
Resident code, INIT, initial stacks, MZ relocations, and placement records move
by the same delta. The directive does not move the initial compressed-file
staging buffer. Earlier M16 implementations that used it as a staging-buffer
selector implemented the wrong meaning; that behavior is superseded.

Non-default placement uses a temporary unpack workspace in the last 128 KiB of
measured RAM. The complete translated image and INIT/stack envelope must fit
below that workspace and above firmware memory. Invalid, duplicate, wrapped,
or overlapping requests fail closed. For example, 2000h and 3000h are qualified
by the host verifier with 512 KiB; this does not imply that every paragraph
address fits every RAM capacity. The startup display distinguishes the expanded
kernel base, file staging buffer, working carrier, resident target, INIT, and
both stacks. Half-open stack ranges end at the first byte beyond the stack.

RAM-dependent fixes require the failing persisted configuration, alternate-model
coverage, and a working-capacity control before a replacement is described as
verified. See `AGENTS.md` for the evidence and handoff requirements.
