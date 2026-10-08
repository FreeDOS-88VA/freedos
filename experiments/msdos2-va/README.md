# MS-DOS 2.0 for the PC-88VA (English distribution disk)

This directory builds a bootable PC-88VA 2HD disk with Microsoft MS-DOS 2.0
(the MIT-licensed release in `microsoft/MS-DOS`) and a PC-88VA BIOS part. It
is a separate experiment of the FreeDOS-88VA project, not a FreeDOS milestone
and not part of any milestone build. It is unofficial and not supported by
Microsoft or NEC.

Validation: VAEG emulator (see Verification). Hardware: owner report on a
PC-88VA2 (see Hardware report); everything else on hardware is NOT RUN.

## What is built

| Part | Source |
|---|---|
| IO.SYS | `v2.0/pc88va/VAIO.ASM` (PC-88VA BIOS part, derived from `SKELIO.ASM`) linked with the Microsoft-supplied `v2.0/bin/SYSINIT.OBJ` and `SYSIMES.OBJ` |
| Boot sector, FORMAT, SYS | `pc88va/VABOOT.ASM`, `VAFORMAT.ASM`, `VASYS.ASM` (shared with the MS-DOS 4.0 disk) |
| MEMINFO | `pc88va/MEMINFO.ASM` (memory layout report; DOS 2.0 has no MEM) |
| MSDOS.SYS, COMMAND.COM, CHKDSK, DEBUG, DISKCOPY, EDLIN, EXE2BIN, FC, FIND, MORE, RECOVER, SORT | Microsoft-supplied `v2.0/bin` binaries |

The project sources are on the `release/msdos-va` branch of
[FreeDOS-88VA/MS-DOS](https://github.com/FreeDOS-88VA/MS-DOS/tree/release/msdos-va);
`lock.json` pins its commit, the emu2 commit and the SHA-256 of every
Microsoft-supplied input. MASM 5.10 and LINK 3.65 from `v4.0/src/TOOLS` run
under emu2 built from its pinned source.

The published 2.0 source tree cannot rebuild MSDOS.SYS, COMMAND.COM or the
utilities: `IO.ASM` included by `STDIO.ASM` is missing, the `context` macro
is undefined, some modules use 2.11-era symbols, CHKDSK and PRINT do not
assemble, and the utilities that do assemble differ from the release
binaries. With the owner's approval, the disk therefore uses the release
binaries for these parts, as the 2.0 README describes for OEMs. They contain
no IBM PC BIOS calls. SYS and FORMAT are replaced by the PC-88VA programs;
PRINT is not included because PRN output is discarded.

## PC-88VA BIOS part

CON uses the ROM text BIOS and the primitive keyboard queue (ASCII keys only);
CLOCK reads and sets the calendar clock; AUX and PRN discard output; drives
A: and B: are the 2HD floppy drives (1024-byte sectors, 8 per track, 80
cylinders, 2 heads) through the ROM floppy BIOS; the sectors of one track move in one ROM
call, ROM status codes map to DOS errors, and media check reports "not
changed" when the ROM says the drive door has not opened since the last
check (otherwise "don't know"). Conventional memory is
measured at boot; backup-memory settings are not read. Device requests run on
a private stack and clear DF on return; SYSINIT keeps the boot stack. The boot
sector finds IO.SYS and MSDOS.SYS through the FAT and reads runs of consecutive
clusters a track at a time.

## Not included

| Part | Reason |
|---|---|
| Sources of MSDOS.SYS, COMMAND.COM, SYSINIT and the utilities | Cannot be rebuilt from the published 2.0 tree (see above); the release binaries are used. |
| PRINT | PRN discards output, so a print spooler has no use yet. |
| SYS (release) | Copies only the system files and relies on the OEM boot sector; replaced by the PC-88VA SYS, which also writes the PC-88VA boot code. |
| FORMAT.OBJ, FORMES.OBJ | OEM parts to be linked with a machine-specific module; replaced by the PC-88VA FORMAT. |
| MASM, LINK, CREF | Development tools of the release. MASM 1.10 does not start under emu2; it was not tried on the PC-88VA. |
| PROHST, PROFIL | Profiler that the 2.0 README says is not for end users. |
| Documentation files (*.DOC, *.TXT of the release) | Not copied; the disk has README.TXT and LICENSE.TXT. |

## Not implemented in the PC-88VA BIOS part

- Japanese: no Japanese display or input (no front-end processor).
- Keyboard: only keys with an ASCII code; function, cursor and other
  special keys are ignored.
- Screen: no ANSI escape sequences (the ANSI option of SKELIO is not used);
  control codes other than CR, LF and BS are not displayed.
- AUX and PRN: discard output; the RS-232C and printer BIOS are not used.
- Disks: only the floppy drives A: and B: in the 2HD format with 1024-byte
  sectors; no other formats, no hard disk.

## Build

Requires git, make, a C compiler and Python 3.12 on the host.

```sh
git submodule update --init components/msdos components/emu2
git -C components/msdos fetch origin release/msdos-va
python3 -B experiments/msdos2-va/build.py --output build/msdos2-va
```

The disk is `build/msdos2-va/msdos2-pc88va-2hd.d88`; `build-record.json`
lists the source and file digests. Two independent builds produce the same
D88 bytes. `readfile.py IMAGE NAME` copies a root-directory file out of a D88.

## Verification (VAEG)

With the distribution CONFIG.SYS (`FILES=20`, `BUFFERS=10`), CHKDSK reports
557,824 bytes free on the PC-88VA and PC-88VA2 with 640 KiB, and on the VA2
426,752, 295,680 and 164,608 bytes with 512, 384 and 256 KiB.

Exercised on the VA2: boot through the FAT, DATE from the calendar, MEMINFO,
CHKDSK (A: and B:), FORMAT B: /S /V and booting the result, DISKCOPY (the copy
is identical), RECOVER, DEBUG, EDLIN, FC, FIND, SORT, MORE, EXE2BIN, COPY and
DIR.

Not run in VAEG: drive B: as the boot drive, less common options. Hardware:
see below.

## Hardware report

HARDWARE PASS for this scope only, reported by the owner on 2026-10-08 for
preview 1 (`msdos2-va.1`, before the track-at-a-time disk transfer): the
released D88 (SHA-256 `fc43456358773809d105a902b5fcd9a7ecd166f6a5b671176ba0194a43f9056e`) written to a
real 2HD diskette booted from drive A: on a PC-88VA2 with 640 KiB installed and 640 KiB
retained in backup memory, and `DIR` and `CHKDSK` ran. Everything else is
NOT RUN on hardware: the PC-88VA, other memory sizes, other commands,
writing to disks, FORMAT and SYS.
