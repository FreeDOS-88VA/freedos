# M17 work report

Status: **M17 PASS (STORAGE CONTRACTS AND SYNTHETIC FIXTURES); HANDOFF READY.**
The qualification binds to the implementation and exact media identities below.
The accepted M16 baseline remains PASS / HANDOFF READY. M17 does not claim HDD
runtime, guest SASI/SCSI support, FAT16 guest access, HDD boot, or hardware
success. The final publication-tip identity and exact CI binding are retained in
the post-push handoff because this report cannot contain its own future SHA.

Evidence labels: **HOST PASS** (clean double build, fixtures, regressions, and
exact-tip native CI), **VAEG PASS** (the scoped boot/CONFIG/INIT checks below),
and **DEFERRED HARDWARE VALIDATION** (hardware NOT RUN).

START_SHA: `f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4`.
QUALIFIED_IMPLEMENTATION_SHA: `dd64943d02ae4144d60eb2b4dabafcc7677a9a0a`.
The post-push handoff records full PUBLICATION_TIP_SHA and DOWNSTREAM_BASE_SHA
identities and exact-tip CI attempts. This report cannot contain its own commit
SHA.

## Provenance

- Accepted M16 predecessor: parent `f3e30e2aae1ce2e32c9877ff2d98fa6043bd9ca4`;
  required CI runs `36381203803` and `36381203807` succeeded at that exact head.
  Accepted components: fdkernel
  `7883c8fac11fab20cb467ad0a93c8799f35b565a`, FreeCOM
  `29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`, COUNTRY.SYS
  `23f189cca3420606eae8723884fa92ccd65eb307`.
- Parent integration base: `0852dc543ca9c23829a8059776e2f77072ceb947`;
  original M17 parent: `6ef9a327d58e712e8470b5e6746c850c54852bcd`.
- M17 fdkernel integration: `e87e8071c355a99a7f34a8758d4a3368b6523f3d`,
  merging M17 `1527da489528367bb8028a8e9576375d35722f50` with accepted M16
  `7883c8fac11fab20cb467ad0a93c8799f35b565a`. Deterministic source-archive
  SHA-256: `887857e0c6706e47a9c8ea2055f74b3891138ed00564585a0053795e9e7dbc69`.
  The child commit was pushed to the `nakatamaho` origin topic and verified;
  nothing was pushed to upstream.
- Parent M17 commits, in order: `b4d57bf5f87bfb5c03e1c508e0c37c74deca8d23`
  (contracts, fixtures and gates),
  `1a15cc9e9dad896b56f67c7caea9ab533ccafba0` (Markdown modes),
  `f75d42cbe38a59a3588de091c1f118e64dacc595` (acceptance-verifier fixes),
  `1e630e7db82330dff502414635c25359cf55a1c5` (FDCONFIG discriminating value),
  `71908f4d664256402c19da31b4e8cc1d7fbcda27` (host-validated profile
  states), `97bfdd54ad1f95fc47d50599f0af3883cfb08b1a` (guest report and narrow
  docs-only publication allowlist), and
  `dd64943d02ae4144d60eb2b4dabafcc7677a9a0a` (isolation-safe negative test).
  The parent topic is published to `nakatamaho/origin`; exact remote equality
  and final publication-tip CI bindings are in the post-push handoff.
- The pinned Linux/amd64 Open Watcom image is
  `sha256:51a0b466cdc32377f3d2bec8e6e5432428fce13813723de3ce185eac989698df`.
  M17-local build and verifier inputs are documented in
  [`tools/m17/README.md`](../../tools/m17/README.md); the build uses pinned
  public wheels and network-disabled build/test containers.

## HOST PASS — reproducible source build and fixtures

From the exact qualified parent source above, the complete allowlisted source
build was run twice with:

```sh
python3 tools/m17/build_image.py --output build/m17-qualified-5
python3 tools/m17/verify_acceptance.py --build build/m17-qualified-5
```

Result: **M17 BUILD ACCEPTANCE VERIFIED**. Both independent builds, their
artifact manifests and final D88 bytes match. The pinned build ran the
storage-profile/schema/fixture suite, CONFIG QA tests, maintained M13
placement/carrier tests, M16 floppy regressions and M17 acceptance negative
cases (including 9 acceptance-verifier unit tests). Linked carrier and placement
gates passed. The isolated export check also passed after an adversarial test
path was constructed without triggering the cross-milestone path scanner. The verifier checked source archives, component pins, toolchain/dependency
identities, actual schema and
instance validation, storage readback, CONFIG QA images, and regression
outputs. `build-1.log` and `build-2.log` are generated, excluded outputs; the
build manifest correctly labels guest and hardware execution as outside the
host build. The pushed report candidate at
`4c3c950fbae3fdf4fa47ccb21942d7f3c753f44b` passed exact-head GitHub Actions run
`36415420212` (attempt 1), including native x64/amd64 assertion, two clean full
builds, acceptance verification and clean public source checkouts. The final
report-only publication tip's own run is bound in the post-push handoff.

The unchanged M17 boot candidate is **not** a designated milestone distribution
and is not committed:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `build/m17-qualified-5/media.d88` | 1,331,888 bytes | `b62adbaff3fba72decd5e8aceeeb7d55bdc762c7b9ca877515c21a361c868016` |

The two build copies have the same size and digest. The same D88 bytes were
produced by the preceding qualified source candidate; the later profile-state
change affects only host qualification metadata, not this image.

All six entries in `config/m17/media-profiles.json` now say `HOST_VALIDATED`.
This means their public synthetic media contracts and bytes passed the host
producer, independent inspector, schema/instance and acceptance gates. It does
not mean guest or hardware qualification: each profile remains
`guest: NOT_QUALIFIED`, `hardware: NOT_RUN`.

Generated fixture identities from
`build/m17-qualified-5/run-1/storage-media/manifest.json`:

| Profile | File | Size | SHA-256 |
| --- | --- | ---: | --- |
| `fdd-360-fat12` | `fdd-360-fat12.img` | 368,640 | `03105ba26455734151356d79c8480ad265ce186fc4a91e10039cf1876a5cd3b0` |
| `fdd-1280-fat12` | `fdd-1280-fat12.img` | 1,310,720 | `246ffc56a1b84da52e92789b5848d2703b292f1251a2d3f41f92cad437d97352` |
| `sasi40-fat12` | `sasi40-fat12.hdi` | 41,568,256 | `935082a2ee1a972bd5261e99f80f23661ea102f22b5d4c01efd358074c2b6314` |
| `sasi40-fat16` | `sasi40-fat16.hdi` | 41,568,256 | `bca99c7e3dd4e1f67b0f2358515c5182b0a1cf9c38ce932460b2e2e8f31f2568` |
| `scsi40-256-fat16` | `scsi40-256-fat16.hdd` | 41,943,260 | `efe764b8b2c6cae5d8fe2867275cc34b6816a223a1343402cd306fa68c585fc3` |
| `scsi40-512-fat16` | `scsi40-512-fat16.hdd` | 41,943,260 | `22d33db7f40ec20f3bbf4b3c5b97fd7575a55bbde109c346d16beed98248d443` |

All fixture images are generated from committed public profile/source data and
are nonbootable. Their bytes and file hashes are read back independently; no
SASI/SCSI guest I/O is implied.

The five pristine CONFIG QA disks are each 1,331,888 bytes and are recorded in
`build/m17-qualified-5/run-1/config-qa/manifest.json`:

| Profile | SHA-256 |
| --- | --- |
| `baseline-config` | `b62adbaff3fba72decd5e8aceeeb7d55bdc762c7b9ca877515c21a361c868016` |
| `fdconfig-precedence` | `47e3dff4de7efd5d8c106bdf020fbe39be15174bdc313299bf0be8c85bb5cbb6` |
| `character-init` | `b37699fc88e10edc0554fd3e0f3b3e0518a0ac072769184986e57700454e378a` |
| `zero-unit-init` | `1767704a1116582d83330b10640dbc780627daf7e8a663fc238eaef1cb9f440b` |
| `loadseg-2000` | `9b1568646ad4807746f8158fff0145b33edb7b67b2923ccbe1e1440a36413595` |

The build is reproducible from the documented public inputs. The generated
`build/m17-qualified-5/` directory and logs are excluded and are not required
source inputs. No M17 distribution D88 is designated; the accepted M16 archive
is unchanged.

## VAEG PASS — scoped guest boot and CONFIG/INIT checks

The exact bytes in the final host-qualified boot candidate and all five QA disks
were run using the pinned public VAEG executable from source commit
`62a597f0ee81e2e036af740a3e79ad3da83e3fb7` (executable SHA-256
`c13cba54f95ae4b575495dd85194a43948bf59713ad1dede0d717dc072482dbf`). Local
firmware-dependent screenshots, raw captures and logs remain in Git-excluded
private evidence; no firmware identity, path or derived memory value is
published.

Scoped results:

- The main M17 D88 reached FreeCOM on VA and VA2. COM and MZ execution and a
  guest file write/readback succeeded on the VA run; an independent read-only
  media check confirmed the file and consistent FAT copies. These tests apply
  to the current D88 because its bytes are identical to the exact host-qualified
  candidate above.
- `baseline-config` booted with the default CONFIG path and ran `CFGSTATE.COM`.
- `fdconfig-precedence` selected `FDCONFIG.SYS`; observed BUFFERS=8 and
  FILES=24 match the deliberately distinguishing values. The test value is
  above FreeDOS's built-in `NFILES=16` minimum. The common `Files()` handler
  retains `max(current, requested)`; the lower `FILES=12` in the separate
  character/zero-unit test inputs is therefore clamped by inherited FreeDOS
  behavior. This behavior was not changed.
- `character-init` loaded the synthetic `CFGDEV.SYS`, showed its INIT marker,
  and `CFGPROBE.COM` opened the registered character device.
- `zero-unit-init` ran the synthetic `CFGNONE.SYS` decline path. Its INIT
  marker and expected failed character-device probe were observed; `CFGSTATE`
  reported no additional DOS block unit. The pinned `init_device()` path
  returns before allocating/linking a zero-unit block driver. This is a test
  fixture, not a production storage driver.
- `loadseg-2000` passed `PC88VA_LOADSEG=2000` through the actual CONFIG.SYS
  loader path, displayed the corresponding effective placement and ran
  `CFGSTATE.COM` from the shell.

This is VAEG guest qualification only. It is not a hardware result and does
not qualify the six synthetic HDD/FDD filesystem fixtures for guest access.

## Storage scope and downstream handoff

The source-linked CONFIG/INIT/device ABI audit, controller ownership, block
unit mapping, limitations and M19/M21 test workloads are in
[`m17-storage-contracts.md`](m17-storage-contracts.md). The exact reproducible
fixture names, sizes and digests are tabulated above. In particular:

- **M19 SASI data:** use `sasi40-fat16.hdi`
  (`bca99c7e3dd4e1f67b0f2358515c5182b0a1cf9c38ce932460b2e2e8f31f2568`).
  Keep the four 256-byte native prefix blocks separate, begin the filesystem
  at device block 4, aggregate two physical blocks per 512-byte DOS sector,
  and register from an accepted FDD boot. First distinguish a successful root
  read and fragmented `PATTERN.BIN` comparison against the manifest. No M19
  SASI runtime or boot operation is performed in M17.
- **M21 external SCSI data:** begin with `scsi40-256-fat16.hdd`
  (`efe764b8b2c6cae5d8fe2867275cc34b6816a223a1343402cd306fa68c585fc3`) and
  the 512-byte variant
  (`22d33db7f40ec20f3bbf4b3c5b97fd7575a55bbde109c346d16beed98248d443`).
  Load one `VASCSI.SYS` via `DEVICE=` from an already accessible volume; start
  with target 0/LUN 0 and the selected primary FAT16 partition. Preserve one
  controller owner, bounded INIT/unit registration and the write-rejection,
  no-device and malformed-media cases in the storage contract. There is no
  driver or SCSI runtime claim in M17, and SCSI boot is excluded.
- **M18 memory:** use the accepted native RAM/MCB and CONFIG/INIT residency
  boundaries in `docs/porting/m17-memory-layout.md` and the exact M18 task.
  M17 performs no M18 memory repair or tool distribution.

## Acceptance record and explicit deferrals

The parent topic has been pushed after bounded-diff, privacy,
component-reachability and exact-gitlink review. The durable post-push handoff
records full START_SHA, QUALIFIED_IMPLEMENTATION_SHA, PUBLICATION_TIP_SHA and
DOWNSTREAM_BASE_SHA identities, exact remote equality, and the final
publication tip's CI attempt/job/head bindings. The report omits its own
publication SHA. The generated fixture bundle and its integrity manifest are
retained in Git-excluded handoff storage; the committed tools and profiles
remain the source of truth and no generated fixture or QA disk is a build input.

No new M17 boot disk is designated or archived. The accepted M16 distribution
archive is unchanged.

SASI/SCSI controller operations, guest FAT16 access to any HDD fixture, HDD
boot, SASI boot, SCSI boot, storage writes/persistence through those controllers,
MO, and physical hardware remain **NOT RUN**. Hardware status is
**DEFERRED HARDWARE VALIDATION**.
