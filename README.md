# FreeDOS PC-88VA Integration

Experimental FreeDOS port for NEC PC-88VA/VA2, built reproducibly from public sources. Organization overview: [FreeDOS-88VA](https://github.com/FreeDOS-88VA).

## Latest: M20.1

**M20 restarts the port on the FreeDOS 1.4 release sources** (kernel `ke2043`, FreeCOM `com086`) with selectively imported changes. **M20.1** is the current M20 release: the floppy disk code transfers a track per ROM call instead of a sector, which cuts floppy commands several-fold. It has **HOST PASS** for the reproducible public build, **VAEG PASS** for the bounded VA/VA2 checks, and an owner hardware report: it boots on a real PC-88VA2 with 640 KB and runs DIR and CHKDSK, with noticeably faster disk access than M20 (**HARDWARE PASS for that scope only**; everything else is NOT RUN on hardware).

- [M20.1 release and downloads](https://github.com/FreeDOS-88VA/freedos/releases/tag/m20.1) (M20, release candidate 5: [tag m20](https://github.com/FreeDOS-88VA/freedos/releases/tag/m20))
- [Release notes](docs/releases/m20.md), [image identities and licenses](images/milestones/m20/README.md), [M20 report](docs/porting/m20-report.md)

Three native 2HD FAT12 floppies (English only):

| Disk | Contents |
|---|---|
| System (A:, bootable) | kernel, shell menu (FreeCOM or MS-DOS 4 COMMAND), EDLIN, MORE, MEM, JWASMR, DEBUG, FORMAT, CHKDSK, SYS |
| Utilities (B:) | FIND, SORT, XCOPY, LABEL, MOVE, APPEND, NLSFUNC, DEVLOAD, CHOICE, DELTREE, COMP, FC, ATTRIB, TREE, REPLACE, EXE2BIN |
| Archivers and tools (B:) | UNZIP, ZIP, GZIP, DEBUG (need 640 KiB) |

Use writable copies in a supported VA/VA2 emulator; no ROM or private firmware is distributed. 640 KiB installed RAM is the qualified setting for JWASMR and the archivers. Not ported: UNDELETE, SWSUBST, SHARE; FAT32 is off; Japanese support is planned for the next milestone.

### Known issues

- Hardware is untested; the stable M18 and M19 Preview 1 kernels have a startup-key (F5/F8) defect that M20 fixes.
- Low-memory limits (384 KiB: JWASMR; 256 KiB: SORT, XCOPY, MOVE) are listed in the release notes.

### Rebuild M20 from public source

```sh
git clone --recurse-submodules https://github.com/FreeDOS-88VA/freedos.git
cd freedos
git checkout <qualified commit from images/milestones/m20/manifest.json>
git submodule update --init --recursive
make m20-toolchain
make m20-disk
make m20-accept
```

Docker (Linux/amd64) and host NASM are required; the pinned Open Watcom 1.9 is acquired by `make m20-toolchain`. The three D88 files are built twice in clean exports and must match the hashes in the release notes. No previous disk or saved DOS binary is an input. Component source stays in its own repository under the [FreeDOS-88VA organization](https://github.com/FreeDOS-88VA); this repository pins exact commits (`manifests/m20-components.lock.json`).

## Earlier releases

- **M19 MS-DOS 4 COMMAND preview**: [prerelease `m19-msdos4-preview.1`](https://github.com/FreeDOS-88VA/freedos/releases/tag/m19-msdos4-preview.1); see the [M19 report](docs/porting/m19-report.md).
- **M18** (stable, emulator-validated only): see below.

## M18 release (stable) — emulator-validated only

**M18 is released with emulator validation only (エミュレータ検証のみ).**
The evidence is **HOST PASS** for the reproducible public-source build and
**VAEG PASS** for the bounded VA/VA2 workflows. Hardware compatibility is
**not qualified**: **DEFERRED HARDWARE VALIDATION**, not `HARDWARE PASS`.

- [M18 release and downloads](https://github.com/FreeDOS-88VA/freedos/releases/tag/m18)
- [Release notes](docs/releases/m18.md)
- [Exact image, source/toolchain identities and licenses](images/milestones/m18/README.md)
- [Validation scope and historical results](docs/porting/m18-report.md)

The release provides one bootable native 2HD FAT12 D88, with FreeCOM,
English/ASCII EDLIN, MORE, MEM, real-mode JWASMR, profile-bounded FORMAT,
CHKDSK and SYS, and small COM/MZ source examples. `HELLO.DOC` on the disk
explains `HELLO.ASM` and its assembly command. The corresponding-source and
license bundle is a host-side companion, **not another floppy**. No ROM or
private firmware is distributed or required to build the disk.

Use a writable copy in the supported emulator. The small complete
edit/assemble/run workflow requires **640 KiB installed RAM**, not merely a
retained BIOS selection; arbitrary source sizes are not guaranteed.
512-KiB sample JWASMR assembly and 256-KiB EDLIN editing are not passes.
SASI/SCSI and hard-disk boot are not part of M18.

### Known issues and M19's first task

- **JWASMR can hang on physical hardware before Usage appears**, including
  an invocation without arguments. Its cause is not established; this is not
  a RAM-failure diagnosis. Fixing and checking this startup issue is
  **M19's first task**, before its planned SASI-data work. See the
  [M19 entry task](docs/tasks/M19-first-task-jwasmr-hardware-startup.md).
  M19 implementation has not started. VAEG success does not qualify this path
  on a real machine.
- Redirected `CHKDSK A:` output can be empty
  ([issue #12](https://github.com/FreeDOS-88VA/freedos/issues/12)); it is
  not counted as a successful A: filesystem check.

### Owner-provided release illustration

![M18 owner-provided photo, with EXIF/GPS removed and diagnostics unmasked](https://github.com/FreeDOS-88VA/freedos/releases/download/m18/freedos-pc88va-m18-public-photo.jpg)

Published with the owner's authorization: EXIF/GPS metadata is removed,
while displayed diagnostics remain unmasked. The same
[metadata-free photograph](images/milestones/m18/freedos-pc88va-m18-public-photo.jpg)
is versioned in the M18 branch and attached to the release. It is an
illustration, **not hardware acceptance or proof of the exact release disk**,
and never a build input. The original metadata-bearing photo is not committed.

## Rebuild M18 from public source

```sh
git clone --branch m18 --recurse-submodules https://github.com/FreeDOS-88VA/freedos.git
cd freedos
make m18-toolchain
make m18-disk
make m18-accept
```

Set up Docker/Linux amd64, the identity-pinned official Open Watcom 1.9
archive and host test dependencies as described in the
[M18 build/setup guide](tools/m18/DISTRIBUTION-README.md) and
[M18-local tooling instructions](tools/m18/README.md). The complete disk is
built twice in clean allowlisted source exports; no previous D88 or saved DOS
executable is an input. Normal outputs are:

- `dist/m18/freedos-PC88VA-M18-2HD.D88`
- `dist/m18/freedos-PC88VA-M18-SOURCES.tar.xz`

The D88 must match SHA-256
`ace43378a504b1af5bad3d6e89184c1e193d6abf85c995b7a94b581a7d743e5c`.
The release's attached source bundle is bound to qualified implementation
`99a8f59a0ec7388cc16968a8814aa23bb0ba8c92`; rebuilding the documentation-only
release tag gives the same D88 but a different source bundle's parent identity.
See the release notes for the exact qualified-bundle checksum and rebuild pin.

Component source remains in its pinned public repositories; project-authored
platform adapters and build recipes are versioned here. Kernel and FreeCOM
use the project forks (now in the `FreeDOS-88VA` organization), not direct
upstream branch changes. All five pinned
components and their source/license identities are recorded in
`manifests/m18-components.lock.json`.

## Historical milestones and project scope

M13-M17 results remain historical, separately bounded qualification; M18 does
not rewrite their acceptance state. See the
[M13-M32 roadmap](docs/freedos-pc88va-milestones-M13-M32.md).

The host scaffold check is `make verify-scaffold`. M01's container build proves
only reproducibility of its pinned upstream baselines, not PC-88VA bootability.
VAEG, licensed ROMs and private verification material are separate inputs for
optional emulator testing, never public-build inputs. Unrun tests are not
passes, and the release photograph does not change the validation boundary.
