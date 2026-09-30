# M18 single native 2HD FreeDOS distribution

`freedos-pc88va-m18-2hd-1280.d88.xz` is the **only designated M18 disk**.
It contains one bootable PC-88VA 80-cylinder, two-head, eight-sector/track,
1024-byte/sector FAT12 2HD disk. The compressed archive is 303,000 bytes,
SHA-256 `e399db6aa1775e3b61f76f1b6e9bb7abcb80de35271f1b0d34ff75dc7d18d5dc`.
The decompressed D88 is 1,331,888 bytes, SHA-256
`ace43378a504b1af5bad3d6e89184c1e193d6abf85c995b7a94b581a7d743e5c`.
See [manifest.json](manifest.json) for complete source/component/toolchain identities,
license references, separate source-bundle digest and qualified test scope.

## Extract and independently check

```sh
xz -t images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz
xz -dc images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz > /tmp/freedos-PC88VA-M18-2HD.D88
sha256sum images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz /tmp/freedos-PC88VA-M18-2HD.D88
```

Use a **writable copy** when testing in a supported VA/VA2 emulator. The
qualifying executable SHA-256 and source revision are in the manifest; its
licensed ROMs are supplied separately by the operator. For normal boot select
that emulator's VA or VA2 model, 640 KiB **installed** for the included small
EDLIN/JWASMR edit/assemble/run samples, this disk as FDD1 and an empty FDD2.
Read `HELLO.DOC` on the disk for the individual COM program explanation and
build steps; `HELLO.ASM` includes its own assembly command.
The public build neither obtains nor invokes an emulator or ROM. Installed
512 KiB (including a stale larger retained setting) is qualified for editing
and native 2HD B: maintenance, **not** for the sample JWASMR assembly. Physical
hardware is **not qualified**: M18 is released with **emulator validation
only**. The complete hardware gate is NOT RUN, and an owner-reported JWASMR
hang before Usage remains a known issue and **M19's first task**. No HARDWARE
PASS or physical repair is claimed. See the
[release notes](../../../docs/releases/m18.md) and
[M18 report](../../../docs/porting/m18-report.md) for the exact scope and
CHKDSK A: redirection caveat.

## Rebuild from public source, not an old disk

From a fresh checkout of `https://github.com/nakatamaho/freedos-pc88va.git`:

```sh
git checkout 99a8f59a0ec7388cc16968a8814aa23bb0ba8c92
git submodule update --init --recursive
make m18-toolchain
make m18-disk M18_DIST=dist/m18
make m18-accept M18_DIST=dist/m18
sha256sum dist/m18/freedos-PC88VA-M18-2HD.D88 dist/m18/freedos-PC88VA-M18-SOURCES.tar.xz
```

Follow [the source/toolchain setup guide](../../../tools/m18/DISTRIBUTION-README.md)
for Docker on Linux/amd64, the pinned official Open Watcom archive, host NASM
and the identity-pinned Unicorn test wheel. `make m18-disk` exports only the
committed M18 inputs and component gitlinks, builds the **complete** disk twice
in separate clean network-disabled containers, and checks placement and media
readback. It does not read a candidate D88 or saved DOS programs. The built
D88 must have the uncompressed digest above; the public-source/license
companion `dist/m18/freedos-PC88VA-M18-SOURCES.tar.xz` must be 2,225,716 bytes, SHA-256
`6283512d3002c67a7b118fecdbb373cb7789d62e03bcf62abb9fbcddbd3470d4`.
The `freedos-` prefix changes host filenames, not disk contents: a clean
build compared byte-for-byte with the HELLO.DOC guest-qualified D88. Its
existing guest scope is retained; this rename is not a new VAEG/hardware run.
The source bundle is a host-side **generated** companion and is not a second
floppy or a committed artifact. Its archives include the exact corresponding
project and component source and their license files. Unmodified official
Open Watcom 1.9 runtime source is available separately from the public URL and
hash in the manifest and on-disk notices. No proprietary ROM is included.

The designated compression used XZ Utils 5.2.5 inside the same identity-checked
Linux/amd64 toolchain container (`xz -c -9e --threads=1 --check=crc64`). To
reproduce its exact compressed bytes without depending on a host `xz` version:

```sh
cid=$(docker create --platform linux/amd64 --network none \
  --entrypoint /usr/bin/xz freedos-pc88va-m18:local \
  -c -9e --threads=1 --check=crc64 /work/freedos-PC88VA-M18-2HD.D88)
docker cp dist/m18/freedos-PC88VA-M18-2HD.D88 "$cid:/work/freedos-PC88VA-M18-2HD.D88"
docker start -a "$cid" > /tmp/recompressed-m18.d88.xz
docker rm "$cid"
cmp /tmp/recompressed-m18.d88.xz \
  images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz
```

Only the D88 xz archive is exempt from the generated-artifact prohibition.
Separate allocator and B: fixture media, emulator outputs, screenshots and
private firmware were never included in this archive.
