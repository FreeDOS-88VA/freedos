# M20 FreeDOS 1.4 based PC-88VA disk set (designated from release candidate 5)

Three designated disks (system, utilities, archivers) as xz archives; see [manifest.json](manifest.json) for digests, source/toolchain identities, license references and the validation scope, and the [release notes](../../../docs/releases/m20.md) for downloads, limits and the rebuild procedure.

```sh
xz -t *.xz
xz -dc freedos-pc88va-m20-2hd-1280.d88.xz | sha256sum
```

Use a writable copy in a VA/VA2 emulator. Hardware is NOT RUN.
