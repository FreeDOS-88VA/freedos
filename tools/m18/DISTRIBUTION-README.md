# PC-88VA FreeDOS M18 native 2HD build

This directory is a generated, public, host-side distribution candidate. It is
not the QA build tree and does not itself imply guest, emulator, VAEG, or
hardware qualification. `build-manifest.json` identifies the exact parent and
component commits, public source-archive hashes, pinned Linux/amd64 toolchain,
source bundle, image bytes, and validation scope. The complete corresponding
sources, build recipes, and licenses are supplied separately in
`PC88VA-M18-SOURCES.tar.xz`; `package-manifest.json` provides versions, build
settings, source identities, output hashes, and declared DOS CPU scope.

## Rebuild from public sources

1. Check out the exact `parent_revision` in `build-manifest.json` from the
   public parent repository and initialize its pinned submodules with
   `git submodule update --init --recursive`.
2. Verify every source archive and child gitlink against
   `PC88VA-M18-SOURCES.tar.xz`'s `SOURCE-MANIFEST.json` and the committed
   `manifests/m18-components.lock.json`.
3. Install Docker and Python 3, then run `make m18-toolchain` to acquire the
   identity-pinned official Open Watcom 1.9 archive and prepare the isolated
   Linux/amd64 build image.
4. Run `make m18-disk`. It builds twice in network-disabled containers from
   deterministic Git exports, verifies independent D88 bytes and native FAT12
   readback, and places identical output under `dist/m18/`.

`make m18-clean` removes only the marker-validated ignored intermediate build
root. The designated distribution is preserved. A different source revision
or output requires a new `M18_DIST` path; the build never overwrites an
unrelated or previously designated disk.

## Disk scope and files

The image is one PC-88VA native 2HD floppy: 80 cylinders, two heads, eight
1024-byte sectors per track, 1280 logical sectors, FAT12, and a fixed English /
ASCII environment. It is not the distinct 2HC profile. The boot path is
intended for the native VA floppy interface; support by any emulator or real
machine must be established by the recorded guest/hardware tests, not inferred
from host construction.

The DOS tool set is deliberately compact: FreeDOS kernel, FreeCOM, COUNTRY.SYS,
EDLIN, MORE, MEMMAP, JWASMR, and the M18 2HD-only CHKDSK, FORMAT, and SYS tools.
The DOS applications and assembly examples target 8086 real mode, do not
require a protected-mode extender, XMS, EMS, or an FPU, and do not change
FreeDOS version reporting. JWASMR is a real-mode DOS16 build of JWasm 2.20;
`JWASM.LIC` contains its Sybase Open Watcom Public License 1.0. `COPYING`
contains the GNU GPL version 2 terms for GPL-covered files. The source bundle
contains the full component license and notice files.

The maintenance programs accept only the documented native 2HD FAT12 profile.
CHKDSK is read-only. FORMAT initializes filesystem metadata only on a B:
volume with a readable, valid native 2HD BPB from prior preparation; it does not
low-level format tracks. SYS requires a valid M18 A: source and a prepared 2HD B: target. FORMAT and SYS
are destructive and should be tried only on disposable media, never on a
release master. These tools do not provide SASI/SCSI support, hard-disk boot,
FAT16 access, or support for other M16 floppy profiles.

MEMMAP validates and reports the DOS MCB chain only. It does not claim to map
physical memory, BIOS reservations, or DOS-unavailable memory. The host
capacity report describes bytes and clusters, not guest free-memory or actual
workflow peak usage. Consult the milestone report for passed and explicitly
unrun gates; host build success is not guest qualification.

## Rebuild and validation data

- `build-manifest.json`: source, toolchain, archive, image identity, and scope.
- `two-build-comparison.json`: exact result of the two independent D88 builds.
- `capacity-budget.json`: BPB/FAT/root/data-region accounting, per-file hashes
  and clusters, and the configured sample-workflow reserve. Guest peak usage
  remains unmeasured until explicitly recorded.
- `package-manifest.json`: package versions, licenses, 8086/VA scope, exact
  source identities, build recipes/options, DOS MZ allocation accounting, and
  disk payload hashes.
- `PC88VA-M18-SOURCES.tar.xz`: source archives with its own member hashes and
  fixed metadata. Verify its compressed SHA-256 against `build-manifest.json`
  before extraction.

No ROM, firmware image, private disk, guest capture, emulator trace, or
private-derived measurement is a build input or included artifact.
