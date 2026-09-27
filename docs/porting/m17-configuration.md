# M17 kernel configuration

## Two readers, different responsibilities

1. The stage-2 loader examines CONFIG.SYS for PC88VA_LOADSEG before loading the
   carrier. This selector places the whole low resident kernel and its work.
2. The common kernel opens FDCONFIG.SYS preferentially, otherwise CONFIG.SYS.
   `DoConfig(0)`, `DoConfig(1)`, and `DoConfig(2)` process the existing common
   command table in order. The last pass runs after PreConfig2 establishes MCBs;
   it can load DEVICE drivers. PostConfig allocates final buffers, file tables,
   drive tables and stacks. DoInstall executes queued INSTALL commands while
   the VA temporary INIT allocation remains reserved.

PC88VA_LOADSEG is recognized as a no-op by the kernel: relocation has already
happened. Setting it only in FDCONFIG.SYS does not affect the earlier loader.
Put it in CONFIG.SYS even when normal DOS options live in FDCONFIG.SYS.
A missing configuration file leaves the normal defaults. The build includes an
editable CONFIG.SYS with BUFFERS=10, FILES=16, LASTDRIVE=E and DOS=LOW.
BUFFERS counts 1024-byte sector buffers; management bytes are additional.

The temporary M13 PC88VA early return is removed. This uses the selected common
FreeDOS parser, not a replacement parser or a promise of MS-DOS compatibility.

## VA integration corrections

The medium-model INIT caller has a FAR return frame and SS differs from DS.
READ accepts a FAR buffer; INIT_DOSEXEC accepts a FAR parameter block and a
NEAR filename; LSEEK uses the correct FAR Pascal frame. Numeric parser outputs
use FAR pointers on VA. NEAR interrupt blocks and the shell-tail work area are
in DGROUP. The compiler is told that SS and DS differ. The existing final
release barrier protects INIT during INSTALL execution.

GetBiosKey uses DOS console/time services on VA, instead of IBM INT 16h and
0040:006Ch. The common skip/stepping command-tail behavior is retained with a
DS-addressable buffer. This source change does not qualify every interactive
F5/F8/conditional-key sequence; those need their own guest input results.

## Explicit platform limits

Ordinary portable command handlers are enabled, including BUFFERS, FILES,
LASTDRIVE, FCBS, STACKS, BREAK, SHELL/COMMAND, SET, ECHO, COUNTRY, DEVICE,
INSTALL, CHAIN, VERSION, ANYDOS, IDLEHALT and SWITCHAR. Enabled code is not a
claim that every argument or combination has been exercised.

The following options currently report a configuration error on VA:

- MENUCOLOR, MENUDEFAULT and MENU (no qualified native menu interface).
- SCREEN, NUMLOCK and KEYBUF (the original handlers use IBM-specific firmware
  or BIOS data areas).
- BUFFERSHIGH, FILESHIGH, LASTDRIVEHIGH, SHELLHIGH, STACKSHIGH, DEVICEHIGH,
  INSTALLHIGH and DOSDATA (no selected VA high-memory allocation contract).
- DOS options other than LOW, NOUMB and LOW,NOUMB.

These are unavailable features, not unused features. INIT size is a placement
constraint, not justification for silently dropping DOS functionality. The
native replacements/high-memory policy remain follow-up work. The underlying
non-VA implementations are preserved. No 640 KiB, HMA, UMB or IBM BIOS shim is
introduced. Existing FreeDOS parser quirks are not repaired as part of the port.

## DEVICE contract and limits

The fixture CFGDEV.SYS is a disposable character device for qualification, not
a SCSI driver. CFGNONE.SYS returns zero block units and retains no memory.
CFGPROBE.COM opens the installed character device after the shell starts;
CFGSTATE.COM reads actual buffer count, LASTDRIVE, SFT capacity and block-unit
count through INT 21h/AH=52h. They are built from tests/m17 sources and are
available beside the build artifacts; they are not required on a normal disk.

The actual supported scope must be recorded against exact kernel/media and
configuration identities. External block-driver success, SASI volumes, SCSI
volumes and HDD boot are not established by this character-driver check.
