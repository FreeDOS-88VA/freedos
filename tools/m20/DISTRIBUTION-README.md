# PC-88VA FreeDOS M20 native 2HD build

This directory is a generated, public, host-side distribution candidate. It is
not the QA build tree and does not itself imply guest, emulator, VAEG, or
hardware qualification. `build-manifest.json` identifies the exact parent and
component commits, public source-archive hashes, pinned Linux/amd64 toolchain,
source bundle, image bytes, and validation scope. The complete corresponding
project/component sources, build recipes, and licenses are supplied separately
in `freedos-PC88VA-M20-SOURCES.tar.xz`; the unmodified compiler runtime has its own
public upstream source reference below. `package-manifest.json` provides
versions, build settings, source identities, output hashes, and declared DOS
CPU scope.

## Rebuild from public sources

1. Check out the exact `parent_revision` in `build-manifest.json` from the
   public parent repository and initialize its pinned submodules with
   `git submodule update --init --recursive`.
2. Verify every source archive and child gitlink against
   `freedos-PC88VA-M20-SOURCES.tar.xz`'s `SOURCE-MANIFEST.json` and the committed
   `manifests/m20-components.lock.json`.
3. Install Docker and Python 3, then run `make m20-toolchain` to acquire the
   identity-pinned official Open Watcom 1.9 archive and prepare the isolated
   Linux/amd64 build image.
4. Run `make m20-disk`. It builds twice in network-disabled containers from
   deterministic Git exports, verifies independent D88 bytes and native FAT12
   readback, and places `freedos-PC88VA-M20-2HD.D88` and
   `freedos-PC88VA-M20-SOURCES.tar.xz` under `dist/m20/`.
5. Run `make m20-accept M20_DIST=dist/m20` to independently close the actual
   JSON instances, source and toolchain references, source bundle archive
   members, distribution files and FATs. This is a host-only gate; VAEG and
   hardware results require separately bound evidence.

`make m20-clean` removes only the marker-validated ignored intermediate build
root. The designated distribution is preserved. A different source revision
or output requires a new `M20_DIST` path; the build never overwrites an
unrelated or previously designated disk.

## Disk scope and files

The image is one PC-88VA native 2HD floppy: 80 cylinders, two heads, eight
1024-byte sectors per track, 1280 logical sectors, FAT12, and a fixed English /
ASCII environment. It is not the distinct 2HC profile. The boot path is
intended for the native VA floppy interface; support by any emulator or real
machine must be established by the recorded guest/hardware tests, not inferred
from host construction.

The DOS tool set is deliberately compact: FreeDOS kernel, FreeCOM, COUNTRY.SYS,
EDLIN, MORE, MEMMAP, JWASMR, and the M20 2HD-only CHKDSK, FORMAT, and SYS tools.
The DOS applications and assembly examples target 8086 real mode, do not
require a protected-mode extender, XMS, EMS, or an FPU, and do not change
FreeDOS version reporting. JWASMR is a real-mode DOS16 build of JWasm 2.20;
`JWASM.LIC` contains its Sybase Open Watcom Public License 1.0. `COPYING`
contains the GNU GPL version 2 terms for GPL-covered files. The source bundle
contains the full project/component license and notice files. The unmodified
Open Watcom 1.9 DOS compiler runtime statically linked into the executables is
also covered by Sybase Open Watcom Public License 1.0 (`JWASM.LIC`). Its public
upstream source is the [official Open Watcom 1.9 source release](https://github.com/open-watcom/open-watcom-1.9/releases/download/ow1.9/open_watcom_1.9.0-src.tar.bz2),
filename `open_watcom_1.9.0-src.tar.bz2`, SHA-256
`6d303327988ee2dda60cfabebf3f45a9758aee4da117d41cf3153fccb7e5e4bf`.
The archive was independently downloaded and inspected for the compiler-runtime
conversion and software-8087 modules and `license.txt`. It is not inside the
M20 component-source archive: the official compiler **binaries** have their
separate hash/URL lock in the toolchain setup. No upstream Watcom runtime code
was modified by M20. Do not conflate the two independently verified binary
and upstream source identities.

At installed 512 KiB, both tested VA/VA2 models completed editor save/reopen,
MORE paging, memory-chain checks and native 2HD maintenance on a separate B:.
JWASMR's sample COM/MZ builds failed at DOS EXEC allocation with no output and
stable shell/MCB state. The bundled full assembler sample workflow was verified
at 640 KiB installed; a retained 640-KiB selection is not writable 640-KiB
RAM. This is a tested small-workload floor, not a promise for arbitrary input
size or a measurement of live heap peaks.

The maintenance programs accept only the native 2HD FAT12 profile in 80 or
NEC-compatible 77 cylinders. CHKDSK is read-only. FORMAT formats every track of
a blank or used B: disk through the VA floppy BIOS and verifies it (`/T:77` for
77 cylinders, `/Q` for a metadata-only rewrite of a valid native volume). SYS
transfers the boot system to a formatted B: and keeps B:'s own geometry and
label. FORMAT and SYS are destructive and should be tried only on target media
in B:, never on a release master. These tools do not provide SASI/SCSI support,
hard-disk boot, FAT16 access, or support for other floppy profiles.

MEMMAP validates and reports the DOS MCB chain only. It does not claim to map
physical memory, BIOS reservations, or DOS-unavailable memory. The host
capacity report describes bytes and clusters, not guest free-memory or actual
workflow peak usage. Consult the milestone report for passed and explicitly
unrun gates; host build success is not guest qualification.

## Rebuild and validation data

- `freedos-PC88VA-M20-2HD.D88`: one native bootable 2HD distribution disk.
- `build-manifest.json`: source, toolchain, archive, image identity, and scope.
- `two-build-comparison.json`: exact result of the two independent D88 builds.
- `capacity-budget.json`: BPB/FAT/root/data-region accounting, per-file hashes
  and clusters, and the configured sample-workflow reserve. Settled guest
  stages were read back; the owner removed instantaneous peak measurement from
  M20 acceptance, and no such peak is claimed.
- `package-manifest.json`: package versions, licenses, 8086/VA scope, exact
  source identities, build recipes/options, DOS MZ allocation accounting, and
  disk payload hashes.
- `freedos-PC88VA-M20-SOURCES.tar.xz`: source archives with its own member hashes and
  fixed metadata. Verify its compressed SHA-256 against `build-manifest.json`
  before extraction.

No ROM, firmware image, private disk, guest capture, emulator trace, or
private-derived measurement is a build input or included artifact.
