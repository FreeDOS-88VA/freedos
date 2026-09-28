# M17 kernel configuration

## Two readers, different responsibilities

1. The stage-2 loader examines `CONFIG.SYS` for `PC88VA_LOADSEG` before loading
   the carrier. This selects the paragraph base of the whole expanded resident
   kernel and its consecutive work area.
2. The common FreeDOS kernel opens `FDCONFIG.SYS` preferentially, otherwise
   `CONFIG.SYS`. `DoConfig(0)`, `DoConfig(1)` and `DoConfig(2)` process the
   existing common command table in order. The last pass runs after `PreConfig2`
   establishes MCBs and can load `DEVICE=` drivers. `PostConfig` allocates final
   buffers, file tables, drive tables and stacks. `DoInstall` executes queued
   `INSTALL` commands while the VA temporary INIT allocation remains reserved.

`PC88VA_LOADSEG` is a no-op to the later kernel parser because relocation has
already happened. Put it in `CONFIG.SYS`, not just `FDCONFIG.SYS`, even when
normal DOS options are supplied in `FDCONFIG.SYS`. A missing configuration file
leaves the common defaults. The committed default `CONFIG.SYS` has
`BUFFERS=10`, `FILES=16`, `LASTDRIVE=E` and `DOS=LOW`. BUFFERS counts 1,024-byte
sector buffers; management bytes are additional.

The temporary M13 early return is removed. This uses the selected common
FreeDOS parser, not a replacement parser or a promise of exact MS-DOS behavior.
The actual VA source audit and INIT ABI are bound by
`config/m17/source-audit.json` and described in
[`m17-storage-contracts.md`](m17-storage-contracts.md).

## VA integration corrections and limits

The medium-model INIT caller has a FAR return frame and SS differs from DS.
READ accepts a FAR buffer; INIT_DOSEXEC accepts a FAR parameter block and a
NEAR filename; LSEEK uses its correct FAR Pascal frame. Numeric parser outputs
use FAR pointers on VA. NEAR interrupt blocks and the shell-tail work area are
in DGROUP. The compiler is told that SS and DS differ. The existing release
barrier protects temporary INIT storage through INSTALL execution.

GetBiosKey uses DOS console/time services on VA rather than IBM INT 16h and
`0040:006Ch`. The common skip/stepping command-tail behavior is retained with a
DS-addressable buffer. This source change does not qualify every interactive
F5/F8/conditional-key sequence; those require their own guest results.

Ordinary portable command handlers are enabled, including BUFFERS, FILES,
LASTDRIVE, FCBS, STACKS, BREAK, SHELL/COMMAND, SET, ECHO, COUNTRY, DEVICE,
INSTALL, CHAIN, VERSION, ANYDOS, IDLEHALT and SWITCHAR. Enabled code is not a
claim that every argument or combination has been exercised. These currently
report a configuration error on VA:

- MENUCOLOR, MENUDEFAULT and MENU (no qualified native menu interface).
- SCREEN, NUMLOCK and KEYBUF (the original handlers use IBM firmware or BIOS
  data areas).
- BUFFERSHIGH, FILESHIGH, LASTDRIVEHIGH, SHELLHIGH, STACKSHIGH, DEVICEHIGH,
  INSTALLHIGH and DOSDATA (no selected VA high-memory allocation contract).
- DOS options other than LOW, NOUMB, and LOW,NOUMB.

These are unavailable features, not unused features. INIT size is a placement
constraint, not justification for silently dropping DOS functionality. The
native replacements/high-memory policy remain follow-up work. The underlying
non-VA implementations are preserved. No 640-KiB assumption, HMA, UMB or IBM
BIOS shim is introduced. Existing FreeDOS parser quirks are not repaired as part
of the port.

## CONFIG/DEVICE qualification inputs

`config/m17/config-qa.json` defines five separate pristine candidate disks and
records the exact `CONFIG.SYS`/`FDCONFIG.SYS` source, effective LOADSEG and
expected active filename:

| Profile | Distinguishing path | Host artifact role |
| --- | --- | --- |
| `baseline-config` | Default `CONFIG.SYS`, LOADSEG 1000h | Normal parser/default regression |
| `fdconfig-precedence` | Different BUFFERS/FILES in `FDCONFIG.SYS` | Proves FDCONFIG selection by observed kernel state |
| `character-init` | `DEVICE=CFGDEV.SYS` | Positive CONFIG-loaded character-driver INIT/open test |
| `zero-unit-init` | `DEVICE=CFGNONE.SYS` | Block-driver zero-unit case; must add no DOS unit or retained allocation |
| `loadseg-2000` | LOADSEG 2000h in CONFIG plus FDCONFIG override | Exercises non-default LOADSEG through the real early loader and later parser |

The positive and zero-unit drivers are synthetic test fixtures only:
CFGDEV.SYS is a disposable character device for strategy/interrupt, INIT and
open. CFGNONE.SYS returns zero block units and no retained extent. Neither is a
SASI/SCSI implementation or substitute for `VASCSI.SYS`. CFGPROBE.COM opens the
character fixture after the shell starts. CFGSTATE.COM reads configured buffer
count, LASTDRIVE, SFT capacity and registered DOS block-unit count through
INT 21h/AH=52h. CFGMEM.COM requests the largest DOS MCB block, releases it, and
prints the reported paragraph count. These are built from `tests/m17/*.asm` and
are added only to the distinct QA disks, not the ordinary candidate image.

Host-side profile checks establish that every referenced configuration exists,
that the LOADSEG directive agrees with its profile, and that the distinguishing
options/drivers are present. They do not establish the guest results. For a
configuration claim, boot that exact candidate under the recorded VAEG revision
and model, verify the startup banner, run CFGSTATE/CFGMEM/CFGPROBE as applicable,
then exercise a small COM and MZ return-to-shell control and guest file
write/readback. Preserve the pristine candidate digest separately from any
emulator-mutated copy. A test not run remains NOT RUN; a zero-unit host fixture
or assembly-source test is not CONFIG/DEVICE guest qualification.

## Runtime/storage boundary

The M17 source audit records the inherited INIT status predicate caveat; an
external block driver must not rely on it to prevent failed/partial
registration. M17 qualifies only the source ABI, public profile contracts and
host-generated fixtures. No operational SASI/SCSI driver, HDD filesystem read,
FAT16 guest volume, SCSI runtime, SASI boot or HDD boot is established by this
configuration work. See the [M17 report](m17-report.md) for exact current test,
build, CI and guest status.
