# M18 single native 2HD FreeDOS distribution

`freedos-pc88va-m18-2hd-1280.d88.xz` is the **only designated M18 disk**.
It contains one bootable PC-88VA 80-cylinder, two-head, eight-sector/track,
1024-byte/sector FAT12 2HD disk. The compressed archive is 302,316 bytes,
SHA-256 `5d7ebb3dd0a29ec817b58c35a2c1550fdb39b810983eaf5c5c33ea24848c5f60`.
The decompressed D88 is 1,331,888 bytes, SHA-256
`991370d0c075f75153192e94365c3c798c3ca50639aaeb716054ab6c5da4dd12`.
See [manifest.json](manifest.json) for complete source/component/toolchain identities,
license references, separate source-bundle digest and qualified test scope.

## Extract and independently check

```sh
xz -t images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz
xz -dc images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz > /tmp/PC88VA-M18-2HD.D88
sha256sum images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz /tmp/PC88VA-M18-2HD.D88
```

Use a **writable copy** when testing in a supported VA/VA2 emulator. The
qualifying executable SHA-256 and source revision are in the manifest; its
licensed ROMs are supplied separately by the operator. For normal boot select
that emulator's VA or VA2 model, 640 KiB **installed** for the included small
EDLIN/JWASMR edit/assemble/run samples, this disk as FDD1 and an empty FDD2.
The public build neither obtains nor invokes an emulator or ROM. Installed
512 KiB (including a stale larger retained setting) is qualified for editing
and native 2HD B: maintenance, **not** for the sample JWASMR assembly. Physical
hardware is NOT RUN. See the [M18 report](../../../docs/porting/m18-report.md)
for the exact scope and CHKDSK A: redirection caveat.

## Rebuild from public source, not an old disk

From a fresh checkout of `https://github.com/nakatamaho/freedos-pc88va.git`:

```sh
git checkout 679fb32dee9709ca298d70b5168bd0dbbd32d601
git submodule update --init --recursive
make m18-toolchain
make m18-disk M18_DIST=dist/m18
make m18-accept M18_DIST=dist/m18
sha256sum dist/m18/PC88VA-M18-2HD.D88 dist/m18/PC88VA-M18-SOURCES.tar.xz
```

Follow [the source/toolchain setup guide](../../../tools/m18/DISTRIBUTION-README.md)
for Docker on Linux/amd64, the pinned official Open Watcom archive, host NASM
and the identity-pinned Unicorn test wheel. `make m18-disk` exports only the
committed M18 inputs and component gitlinks, builds the **complete** disk twice
in separate clean network-disabled containers, and checks placement and media
readback. It does not read a candidate D88 or saved DOS programs. The built
D88 must have the uncompressed digest above; the public-source/license
companion `dist/m18/PC88VA-M18-SOURCES.tar.xz` must be 2,224,012 bytes, SHA-256
`afcac120b9fcab6a080187d74d06daa97b00f053421d604ea474e3eeac8d341d`.
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
  -c -9e --threads=1 --check=crc64 /work/PC88VA-M18-2HD.D88)
docker cp dist/m18/PC88VA-M18-2HD.D88 "$cid:/work/PC88VA-M18-2HD.D88"
docker start -a "$cid" > /tmp/recompressed-m18.d88.xz
docker rm "$cid"
cmp /tmp/recompressed-m18.d88.xz \
  images/milestones/m18/freedos-pc88va-m18-2hd-1280.d88.xz
```

Only the D88 xz archive is exempt from the generated-artifact prohibition.
Separate allocator and B: fixture media, emulator outputs, screenshots and
private firmware were never included in this archive.
