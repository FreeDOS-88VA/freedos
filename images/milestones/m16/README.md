# M16 FreeDOS PC-88VA distribution

`freedos-pc88va-m16-2hd-1280.d88.xz` is the designated M16 bootable 2HD
distribution. Its compressed and uncompressed identities, source revisions,
toolchain, validation scope, and license references are recorded in
`manifest.json`.

Extract and check the archived image from the repository root:

```sh
xz --test images/milestones/m16/freedos-pc88va-m16-2hd-1280.d88.xz
xz -dc images/milestones/m16/freedos-pc88va-m16-2hd-1280.d88.xz \
  > build/freedos-pc88va-m16-2hd-1280.d88
sha256sum build/freedos-pc88va-m16-2hd-1280.d88
```

To reproduce the disk from a fresh checkout, initialize the pinned component
submodules and follow [`tools/m16/README.md`](../../../tools/m16/README.md) to
install the identity-pinned host toolchain. Check out the `rebuild_source.parent`
revision from `manifest.json`, then run:

```sh
python3 tools/m16/toolchain.py
python3 tools/m16/build_image.py --output build/m16-rebuild --boot-profile 2hd-1280
sha256sum build/m16-rebuild/media.d88
```

`build_image.py` makes two independent clean source-export builds and compares
their artifact manifests and D88 bytes. The output must match the uncompressed
SHA-256 and byte count in `manifest.json`. Do not use cached binaries or prior
milestone images as build inputs.

The distribution was booted in VAEG on VA and VA2. The recorded scope is
emulator validation; physical hardware validation was not run. VAEG and FreeDOS
source identities, guest results, and artifact hashes are kept in the M16
acceptance report and the local private handoff. No ROMs are included.

The parent project is GPL-2.0-or-later; see [`COPYING`](../../../COPYING) and
[`LICENSE.md`](../../../LICENSE.md). Component notices are in the pinned
fdkernel (`COPYING`), FreeCOM (`license` and its SUPPL notices), and COUNTRY.SYS
(`LICENSE`) repositories. Preserve those notices with redistributed source.
