# MS-DOS 4.0 for the PC-88VA (English distribution disk)

This directory builds a bootable PC-88VA 2HD disk with Microsoft MS-DOS 4.0,
assembled and compiled from the MIT-licensed source release
(`microsoft/MS-DOS`) plus a PC-88VA BIOS part. Two prebuilt libraries of that
release, which has no source for them, are linked in (see below). It is a separate experiment of
the FreeDOS-88VA project, not a FreeDOS milestone and not part of any
milestone build. It is unofficial and not supported by Microsoft or NEC.

Validation: VAEG emulator (see Verification). Hardware: owner report on a
PC-88VA2 (see Hardware report); everything else on hardware is NOT RUN.

## Sources

All sources are on the `release/msdos-va` branch of
[FreeDOS-88VA/MS-DOS](https://github.com/FreeDOS-88VA/MS-DOS/tree/release/msdos-va);
`lock.json` pins its commit, the emu2 commit and the SHA-256 of every file in
`v4.0/src/TOOLS`.

| Part | Source |
|---|---|
| MSDOS.SYS, COMMAND.COM, utilities, COUNTRY.SYS | `v4.0/src`, built by the original makefiles |
| IO.SYS | `v4.0/pc88va/VAIO.ASM` (PC-88VA BIOS part) + `v4.0/src/BIOS` SYSINIT1, SYSCONF, SYSINIT2, SYSIMES |
| Boot sector, FORMAT, SYS | `pc88va/VABOOT.ASM`, `VAFORMAT.ASM`, `VASYS.ASM` (shared with the MS-DOS 2.0 disk) |

Prebuilt libraries linked without source in the release:

- `v4.0/src/INC/COMSUBS.LIB` (common routines: case mapping, DBCS checks,
  argument parsing, messages) in BACKUP, RESTORE, JOIN, REPLACE and SUBST;
- `v4.0/src/LIB/MEM.LIB` (a Microsoft C run-time library) in MEM.

As with any C compiler, the C utilities also link the Microsoft C 5.10
run-time libraries in `v4.0/src/TOOLS/BLD/LIB`, and the tools themselves are
the binaries in `v4.0/src/TOOLS`. Everything else on the disk is built from
source.

The build runs the original NMAKE, BUILDIDX, BUILDMSG, NOSRVBLD, MASM 5.10,
CL 5.10, LINK 3.65 and EXE2BIN from `v4.0/src/TOOLS` under emu2 built from its
pinned source, with `PC88VA` defined for assembler and compiler. NMAKE needs a
command interpreter, so COMMAND.COM is first assembled module by module and
the NMAKE-built COMMAND.COM must equal it.

## Changes for the PC-88VA

In `v4.0/src`, every change is conditional on `PC88VA` except one comment fix:

- `BIOS/SYSINIT1.ASM`: skip the IBM INT 11h/15h configuration probes, the
  INT 15h extended-memory query and the shared-interrupt rearm port writes.
- `CMD/APPEND`, `CHKDSK`, `DEBUG`, `MORE`, `SHARE`, `MEM`: do not call
  INT 10h, 12h or 15h, which are hardware interrupt vectors on the PC-88VA.
- `CMD/CHKDSK`, `CMD/RECOVER`: accept 1024-byte sectors and derive the
  directory entries per sector from the sector size.
- `CMD/COMMAND`: CLS uses the VA text BIOS (existing `PC88VA` option).
- `MAPPER/GETMSG.ASM`: one comment line held 66 U+FFFD characters from a
  character-set conversion and exceeded the MASM line limit.

MSDOS.SYS is built from unchanged sources.

The PC-88VA BIOS part provides CON (ROM text BIOS, primitive keyboard queue),
CLOCK$ (calendar clock), AUX/PRN (discarded), and the A:/B: 2HD drives through
the ROM floppy BIOS, with DOS 4 generic IOCTL (device parameters, track
read/write, media ID). It measures conventional memory at boot and ignores
backup-memory settings. The boot sector finds IO.SYS and MSDOS.SYS through the
FAT. FORMAT formats 2HD disks (1024-byte sectors, 8 per track, 80 cylinders,
2 heads); SYS makes a formatted disk bootable.

## Not included

The distribution build does not build these parts. Except where noted, an
earlier trial build of the unmodified tree assembled them, so they are
omitted for function, not for build failures.

| Part | Reason |
|---|---|
| IBM BIOS part of IO.SYS (MSBIO1 ... MSINIT), MSLOAD, BOOT (MSBOOT) | Replaced by the PC-88VA BIOS part and boot sector. |
| FORMAT, SYS (IBM) | Assume 512-byte sectors and the IBM boot sector; replaced by the PC-88VA FORMAT and SYS. The IBM FORMAT did not build in the trial (it needs the BOOT message include). |
| ANSI.SYS, DISPLAY.SYS, KEYBOARD.SYS, PRINTER.SYS, KEYB, GRAFTABL, GRAPHICS, MODE | Program the IBM video BIOS, keyboard, code pages and ports directly. |
| FDISK, DRIVER.SYS | IBM fixed-disk partitioning and IBM diskette parameters. |
| DISKCOPY, DISKCOMP | Assume 512-byte sectors in many places; DISKCOPY also formats tracks through generic IOCTL, which the PC-88VA driver does not implement, and calls INT 13h. Not ported. |
| RAMDRIVE.SYS, VDISK.SYS, SMARTDRV, XMA2EMS.SYS, XMAEM.SYS | Need extended or expanded memory of IBM-compatible machines. |
| MEMM | Expanded-memory manager; not built. |
| PRINT | PRN discards output, so a print spooler has no use yet. |
| DOSSHELL, SELECT | IBM text-mode shell and installer; SELECT also has damaged characters in the published sources. Not built. |
| FILESYS, IFSFUNC | Installable file system support for networks; no file system driver to use it. |

## Not implemented in the PC-88VA BIOS part

- Japanese: no Japanese display or input (no front-end processor).
- Keyboard: only keys with an ASCII code; function, cursor and other
  special keys are ignored.
- Screen: no ANSI escape sequences; control codes other than CR, LF and BS
  are not displayed. Box-drawing characters of TREE and MEM appear as other
  characters of the VA font.
- AUX and PRN: discard output; the RS-232C and printer BIOS are not used.
- Disks: only the floppy drives A: and B: in the 2HD format with 1024-byte
  sectors (8 per track, 80 cylinders, 2 heads); no 2DD or other formats, no
  hard disk. Media change is always reported as unknown, so DOS decides.
  Generic IOCTL format and verify track are not implemented.

## Build

Requires git, make, a C compiler and Python 3.12 on the host.

```sh
git submodule update --init components/msdos components/emu2
git -C components/msdos fetch origin release/msdos-va
python3 -B experiments/msdos4-va/build.py --output build/msdos4-va
```

The disk is `build/msdos4-va/msdos4-pc88va-2hd.d88`; `build-record.json`
lists the source and file digests. Two independent builds produce the same
D88 bytes.

## Verification (VAEG)

With the distribution CONFIG.SYS (`FILES=20`, `BUFFERS=10`, `LASTDRIVE=E`),
MEM reports 533,200 bytes as the largest executable program on the PC-88VA and
PC-88VA2 with 640 KiB. On the VA2 it reports 402,128, 271,056 and 139,984
bytes with 512, 384 and 256 KiB, and 512 KiB is detected with a stale 640 KiB
setting in backup memory. Each run wrote and compared a file.

Exercised on the VA2: boot through the FAT, DATE and TIME from the calendar,
FORMAT B: /S and booting the result, SYS, LABEL, VOL, CHKDSK (A: and B:),
MEM /PROGRAM and /DEBUG, DIR, COPY, XCOPY, MD, TREE, ATTRIB, FC, COMP, FIND,
SORT, MORE, REPLACE, SUBST, JOIN, ASSIGN, APPEND, FASTOPEN, SHARE, NLSFUNC,
CHCP, BACKUP and RESTORE round trip, RECOVER, DEBUG, EDLIN and EXE2BIN.

Not run in VAEG: other utilities' less common options, drive B: as the boot
drive, CONFIG.SYS options beyond those above. Hardware: see below.

## Hardware report

HARDWARE PASS for this scope only, reported by the owner on 2026-10-08: the
released D88 (SHA-256 `9e4baf0e4098d2c6c2e3810fec0a524f1f7a2540ddc9e183241d1cd2941faa2e`) written to a
real 2HD diskette booted on a PC-88VA2 with 640 KiB installed and 640 KiB
retained in backup memory, and `DIR` and `CHKDSK` ran. Everything else is
NOT RUN on hardware: the PC-88VA, other memory sizes, other commands,
writing to disks, FORMAT and SYS.
