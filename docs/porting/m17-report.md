# M17 work report

Status: implementation and qualification in progress. M16 remains partial;
this report does not upgrade its outstanding acceptance or claim HDD runtime.

START_SHA: `fc891f3cd424c281680dd15b3f269bef4a4d2880`.
Predecessor native CI: run 36308581599, attempt 1, successful at START_SHA.
Kernel configuration implementation:
`1527da489528367bb8028a8e9576375d35722f50`.
FreeCOM: `29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`.
COUNTRY.SYS: `23f189cca3420606eae8723884fa92ccd65eb307`.
The manifest and source audit bind exact component archives and reviewed files.

## Implemented

- Restored the selected common kernel configuration passes after the loader's
  separate PC88VA_LOADSEG probe. FDCONFIG.SYS has normal kernel precedence.
- Corrected the VA FAR Pascal READ, LSEEK and INIT_DOSEXEC interfaces, separate
  stack pointer use, numeric argument outputs, command-tail storage and INSTALL
  lifetime. Kept the common parser and non-VA platform behavior.
- Added an editable default CONFIG.SYS. Unavailable native menu/BIOS/high-memory
  options are explicit errors; see m17-configuration.md for the exact boundary.
- Audited DEVICE/header/INIT/DPB/BPB/unit registration. Documented inherited
  status handling, required external block acceptance and bounded M18/M20 work.
- Added six deterministic public FAT12/FAT16 data fixtures, an independent
  container/filesystem reader, malformed-input tests and source audit binding.
- Maintained complete M17-local build/media tools and native CI. Historical
  helper implementation provenance is recorded; historical acceptance is not
  imported. SCSI remains external, native SCSI boot excluded and MO last.

## Verification scope

The preliminary CONFIG candidate completed two full clean builds and the
maintained placement/carrier/buffer gates. Exact guest results remain in excluded
storage. Publication requires the final integrated build and its exact-head CI.
The six storage volumes also passed a supplemental host fsck.fat read-only check;
this is filesystem evidence, not VA storage evidence.

The unchanged guest shell and final work policy retain the ten-buffer default.
The default configuration's linked resident image is 71488 bytes and final
kernel work is 13712 bytes, total 85200 bytes (83.203125 KiB). This is 5264 bytes
more than the preceding CONFIG-disabled checkpoint; the increase restores
configuration storage and required adapter code. INIT is 15835 bytes, temporary,
with its stack anchor unchanged. Per-CONFIG buffers/files/drivers can change the
final work size. Do not advertise a fixed footprint for all configurations.

## Remaining scope and handoff

Host-valid FAT16 images are not guest FAT16 support. SASI discovery/translation/
registration and real data I/O remain M18; native SASI boot remains M19. Actual
external SCSI block INIT/read-only access remains M20, writes M21 and integration
M22. Native menu/high-memory settings and exhaustive interactive CONFIG choices
are not qualified. M16's remaining full input/media acceptance is unchanged.
Hardware is NOT RUN; retain DEFERRED HARDWARE VALIDATION. No milestone archive
is designated by this work checkpoint. Exact implementation/publication/source
and CI bindings must be recorded separately; this report cannot contain its own
publication commit identity.
